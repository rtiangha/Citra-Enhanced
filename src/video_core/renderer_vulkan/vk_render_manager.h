// Copyright 2024 Citra Emulator Project
// Licensed under GPLv2 or any later version
// Refer to the license.txt file included.

#pragma once

#include <bit>
#include <mutex>

#include "common/math_util.h"
#include "video_core/renderer_vulkan/vk_common.h"

namespace VideoCore {
enum class PixelFormat : u32;
}

namespace Vulkan {

class Instance;
class Scheduler;
class Framebuffer;

struct RenderPass {
    vk::Framebuffer framebuffer;
    vk::RenderPass render_pass;
    vk::Rect2D render_area;
    std::array<vk::ClearValue, 2> clears;
    u32 do_clear;

    bool operator==(const RenderPass& other) const noexcept {
        return std::tie(framebuffer, render_pass, render_area, do_clear) ==
                   std::tie(other.framebuffer, other.render_pass, other.render_area,
                            other.do_clear) &&
               std::memcmp(&clears, &other.clears, sizeof(clears)) == 0;
    }
};

class RenderManager {
    static constexpr u32 NumColorFormats = 13;
    static constexpr u32 NumDepthFormats = 4;
    static constexpr u32 NumSamples = 8;
    static_assert(std::has_single_bit(NumSamples));

public:
    explicit RenderManager(const Instance& instance, Scheduler& scheduler);
    ~RenderManager();

    /// Begins a new renderpass with the provided framebuffer as render target.
    void BeginRendering(const Framebuffer* framebuffer, Common::Rectangle<u32> draw_rect);

    /// Begins a new renderpass with the provided render state.
    void BeginRendering(const RenderPass& new_pass);

    /// Exits from any currently active renderpass instance
    void EndRendering();

    /// Returns the renderpass associated with the color-depth format pair
    vk::RenderPass GetRenderpass(VideoCore::PixelFormat color, VideoCore::PixelFormat depth,
                                 bool is_clear, u8 sample_count = 1);

private:
    /// Creates a renderpass configured appropriately and stores it in cached_renderpasses
    vk::UniqueRenderPass CreateRenderPass(vk::Format color, vk::Format depth,
                                          vk::AttachmentLoadOp load_op,
                                          vk::SampleCountFlagBits sample_count) const;

private:
    const Instance& instance;
    Scheduler& scheduler;
    vk::UniqueRenderPass cached_renderpasses[NumColorFormats + 1][NumDepthFormats + 1]
                                            [std::bit_width(NumSamples)][2];
    std::mutex cache_mutex;
    std::array<vk::Image, 4> images;
    std::array<vk::ImageAspectFlags, 2> aspects;
    RenderPass pass{};
    u32 num_draws{};
};

} // namespace Vulkan
