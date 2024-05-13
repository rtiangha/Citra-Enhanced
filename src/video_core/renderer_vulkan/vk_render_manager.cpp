// Copyright 2024 Citra Emulator Project
// Licensed under GPLv2 or any later version
// Refer to the license.txt file included.

#include <limits>
#include <boost/container/static_vector.hpp>
#include "common/assert.h"
#include "video_core/rasterizer_cache/pixel_format.h"
#include "video_core/renderer_vulkan/vk_instance.h"
#include "video_core/renderer_vulkan/vk_render_manager.h"
#include "video_core/renderer_vulkan/vk_scheduler.h"
#include "video_core/renderer_vulkan/vk_texture_runtime.h"

namespace Vulkan {

constexpr u32 MinDrawsToFlush = 20;

using VideoCore::PixelFormat;
using VideoCore::SurfaceType;

RenderManager::RenderManager(const Instance& instance, Scheduler& scheduler)
    : instance{instance}, scheduler{scheduler} {}

RenderManager::~RenderManager() = default;

void RenderManager::BeginRendering(const Framebuffer* framebuffer,
                                   Common::Rectangle<u32> draw_rect) {
    const vk::Rect2D render_area = {
        .offset{
            .x = static_cast<s32>(draw_rect.left),
            .y = static_cast<s32>(draw_rect.bottom),
        },
        .extent{
            .width = draw_rect.GetWidth(),
            .height = draw_rect.GetHeight(),
        },
    };
    const RenderPass new_pass = {
        .framebuffer = framebuffer->Handle(),
        .render_pass = framebuffer->RenderPass(),
        .render_area = render_area,
        .clears = {},
        .do_clear = false,
    };
    images = framebuffer->Images();
    aspects = framebuffer->Aspects();
    BeginRendering(new_pass);
}

void RenderManager::BeginRendering(const RenderPass& new_pass) {
    if (pass == new_pass) [[likely]] {
        num_draws++;
        return;
    }

    EndRendering();
    scheduler.Record([info = new_pass](vk::CommandBuffer cmdbuf) {
        const vk::RenderPassBeginInfo renderpass_begin_info = {
            .renderPass = info.render_pass,
            .framebuffer = info.framebuffer,
            .renderArea = info.render_area,
            .clearValueCount = info.do_clear ? 2u : 0u,
            .pClearValues = info.clears.data(),
        };
        cmdbuf.beginRenderPass(renderpass_begin_info, vk::SubpassContents::eInline);
    });

    pass = new_pass;
}

void RenderManager::EndRendering() {
    if (!pass.render_pass) {
        return;
    }

    scheduler.Record([images = images, aspects = aspects](vk::CommandBuffer cmdbuf) {
        u32 num_barriers = 0;
        vk::PipelineStageFlags pipeline_flags{};
        std::array<vk::ImageMemoryBarrier, 2> barriers;
        for (u32 i = 0; i < images.size(); i++) {
            if (!images[i]) {
                continue;
            }
            const bool is_color = static_cast<bool>(aspects[i] & vk::ImageAspectFlagBits::eColor);
            if (is_color) {
                pipeline_flags |= vk::PipelineStageFlagBits::eColorAttachmentOutput;
            } else {
                pipeline_flags |= vk::PipelineStageFlagBits::eEarlyFragmentTests |
                                  vk::PipelineStageFlagBits::eLateFragmentTests;
            }
            barriers[num_barriers++] = vk::ImageMemoryBarrier{
                .srcAccessMask = is_color ? vk::AccessFlagBits::eColorAttachmentWrite
                                          : vk::AccessFlagBits::eDepthStencilAttachmentWrite,
                .dstAccessMask =
                    vk::AccessFlagBits::eShaderRead | vk::AccessFlagBits::eTransferRead,
                .oldLayout = vk::ImageLayout::eGeneral,
                .newLayout = vk::ImageLayout::eGeneral,
                .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                .image = images[i],
                .subresourceRange{
                    .aspectMask = aspects[i],
                    .baseMipLevel = 0,
                    .levelCount = 1,
                    .baseArrayLayer = 0,
                    .layerCount = VK_REMAINING_ARRAY_LAYERS,
                },
            };
        }
        cmdbuf.endRenderPass();
        if (num_barriers == 0) {
            return;
        }
        cmdbuf.pipelineBarrier(pipeline_flags,
                               vk::PipelineStageFlagBits::eFragmentShader |
                                   vk::PipelineStageFlagBits::eTransfer,
                               vk::DependencyFlagBits::eByRegion, 0, nullptr, 0, nullptr,
                               num_barriers, barriers.data());
    });

    // Reset state.
    pass.render_pass = VK_NULL_HANDLE;
    images = {};
    aspects = {};

    // The Mali guide recommends flushing at the end of each major renderpass
    // Testing has shown this has a significant effect on rendering performance
    if (num_draws > MinDrawsToFlush && instance.ShouldFlush()) {
        scheduler.Flush();
        num_draws = 0;
    }
}

vk::RenderPass RenderManager::GetRenderpass(VideoCore::PixelFormat color,
                                            VideoCore::PixelFormat depth, bool is_clear,
                                            u8 sample_count) {
    std::scoped_lock lock{cache_mutex};

    const u32 color_index =
        color == VideoCore::PixelFormat::Invalid ? NumColorFormats : static_cast<u32>(color);
    const u32 depth_index =
        depth == VideoCore::PixelFormat::Invalid ? NumDepthFormats : (static_cast<u32>(depth) - 14);

    ASSERT_MSG(color_index <= NumColorFormats && depth_index <= NumDepthFormats,
               "Invalid color index {} and/or depth_index {}", color_index, depth_index);

    ASSERT_MSG(sample_count && std::has_single_bit(sample_count) && sample_count <= NumSamples,
               "Invalid sample count {}", static_cast<u32>(sample_count));

    const u32 samples_index = static_cast<u32>(std::bit_width(sample_count) - 1);

    vk::UniqueRenderPass& renderpass =
        cached_renderpasses[color_index][depth_index][samples_index][is_clear];
    if (!renderpass) {
        const vk::Format color_format = instance.GetTraits(color).native;
        const vk::Format depth_format = instance.GetTraits(depth).native;
        const vk::AttachmentLoadOp load_op =
            is_clear ? vk::AttachmentLoadOp::eClear : vk::AttachmentLoadOp::eLoad;
        renderpass = CreateRenderPass(color_format, depth_format, load_op,
                                      static_cast<vk::SampleCountFlagBits>(sample_count));
    }

    return *renderpass;
}

vk::UniqueRenderPass RenderManager::CreateRenderPass(vk::Format color, vk::Format depth,
                                                     vk::AttachmentLoadOp load_op,
                                                     vk::SampleCountFlagBits sample_count) const {

    boost::container::static_vector<vk::AttachmentDescription, 4> attachments{};
    boost::container::static_vector<vk::AttachmentReference, 2> resolve_attachments{};

    bool use_color = false;
    vk::AttachmentReference color_attachment_ref{};
    bool use_depth = false;
    vk::AttachmentReference depth_attachment_ref{};

    if (color != vk::Format::eUndefined) {
        attachments.emplace_back(vk::AttachmentDescription{
            .format = color,
            .samples = vk::SampleCountFlagBits::e1,
            .loadOp = load_op,
            .storeOp = vk::AttachmentStoreOp::eStore,
            .stencilLoadOp = vk::AttachmentLoadOp::eDontCare,
            .stencilStoreOp = vk::AttachmentStoreOp::eDontCare,
            .initialLayout = vk::ImageLayout::eGeneral,
            .finalLayout = vk::ImageLayout::eGeneral,
        });

        color_attachment_ref = vk::AttachmentReference{
            .attachment = static_cast<u32>(attachments.size() - 1),
            .layout = vk::ImageLayout::eGeneral,
        };

        use_color = true;
    }

    if (depth != vk::Format::eUndefined) {
        attachments.emplace_back(vk::AttachmentDescription{
            .format = depth,
            .samples = vk::SampleCountFlagBits::e1,
            .loadOp = load_op,
            .storeOp = vk::AttachmentStoreOp::eStore,
            .stencilLoadOp = load_op,
            .stencilStoreOp = vk::AttachmentStoreOp::eStore,
            .initialLayout = vk::ImageLayout::eGeneral,
            .finalLayout = vk::ImageLayout::eGeneral,
        });

        depth_attachment_ref = vk::AttachmentReference{
            .attachment = static_cast<u32>(attachments.size() - 1),
            .layout = vk::ImageLayout::eGeneral,
        };

        use_depth = true;
    }

    // In the case of MSAA, each attachment gets an additional MSAA attachment that now becomes the
    // main attachment and the original attachments now get resolved into
    if (sample_count > vk::SampleCountFlagBits::e1) {
        if (color != vk::Format::eUndefined) {
            attachments.emplace_back(vk::AttachmentDescription{
                .format = color,
                .samples = sample_count,
                .loadOp = load_op,
                .storeOp = vk::AttachmentStoreOp::eStore,
                .stencilLoadOp = vk::AttachmentLoadOp::eDontCare,
                .stencilStoreOp = vk::AttachmentStoreOp::eDontCare,
                .initialLayout = vk::ImageLayout::eGeneral,
                .finalLayout = vk::ImageLayout::eGeneral,
            });

            resolve_attachments.emplace_back(color_attachment_ref);

            color_attachment_ref = vk::AttachmentReference{
                .attachment = static_cast<u32>(attachments.size() - 1),
                .layout = vk::ImageLayout::eGeneral,
            };
        }

        if (depth != vk::Format::eUndefined) {
            attachments.emplace_back(vk::AttachmentDescription{
                .format = depth,
                .samples = sample_count,
                .loadOp = load_op,
                .storeOp = vk::AttachmentStoreOp::eStore,
                .stencilLoadOp = load_op,
                .stencilStoreOp = vk::AttachmentStoreOp::eStore,
                .initialLayout = vk::ImageLayout::eGeneral,
                .finalLayout = vk::ImageLayout::eGeneral,
            });

            resolve_attachments.emplace_back(depth_attachment_ref);

            depth_attachment_ref = vk::AttachmentReference{
                .attachment = static_cast<u32>(attachments.size() - 1),
                .layout = vk::ImageLayout::eGeneral,
            };
        }
    } else {
        if (color != vk::Format::eUndefined) {
            resolve_attachments.emplace_back(vk::AttachmentReference{VK_ATTACHMENT_UNUSED});
        }

        if (depth != vk::Format::eUndefined) {
            resolve_attachments.emplace_back(vk::AttachmentReference{VK_ATTACHMENT_UNUSED});
        }
    }

    const vk::SubpassDescription subpass = {
        .pipelineBindPoint = vk::PipelineBindPoint::eGraphics,
        .inputAttachmentCount = 0,
        .pInputAttachments = nullptr,
        .colorAttachmentCount = use_color ? 1u : 0u,
        .pColorAttachments = &color_attachment_ref,
        .pResolveAttachments = resolve_attachments.data(),
        .pDepthStencilAttachment = use_depth ? &depth_attachment_ref : nullptr,
    };

    const vk::RenderPassCreateInfo renderpass_info = {
        .attachmentCount = static_cast<u32>(attachments.size()),
        .pAttachments = attachments.data(),
        .subpassCount = 1,
        .pSubpasses = &subpass,
        .dependencyCount = 0,
        .pDependencies = nullptr,
    };

    return instance.GetDevice().createRenderPassUnique(renderpass_info);
}

} // namespace Vulkan
