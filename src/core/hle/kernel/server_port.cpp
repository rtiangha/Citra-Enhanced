// Copyright 2016 Citra Emulator Project
// Licensed under GPLv2 or any later version
// Refer to the license.txt file included.

#include <tuple>
#include "common/archives.h"
#include "common/assert.h"
#include "core/hle/kernel/client_port.h"
#include "core/hle/kernel/errors.h"
#include "core/hle/kernel/object.h"
#include "core/hle/kernel/server_port.h"
#include "core/hle/kernel/server_session.h"
#include "core/hle/kernel/thread.h"

SERIALIZE_EXPORT_IMPL(Kernel::ServerPort)

namespace Kernel {

ResultVal<std::shared_ptr<ServerSession>> ServerPort::Accept() {
    if (pending_sessions.empty()) {
        return ERR_NO_PENDING_SESSIONS;
    }

    auto session = std::move(pending_sessions.back());
    pending_sessions.pop_back();
    return MakeResult(std::move(session));
}

bool ServerPort::ShouldWait(const Thread* thread) const {
    // If there are no pending sessions, we wait until a new one is added.
    return pending_sessions.size() == 0;
}

void ServerPort::Acquire(Thread* thread) {
    ASSERT_MSG(!ShouldWait(thread), "object unavailable!");
}

KernelSystem::PortPair KernelSystem::CreatePortPair(u32 max_sessions, std::string name) {
    auto server_port{std::make_shared<ServerPort>()};
    server_port->Init(*this);
    auto client_port{std::make_shared<ClientPort>()};
    client_port->Init(*this);

    server_port->name = name + "_Server";
    client_port->name = name + "_Client";
    client_port->server_port = server_port;
    client_port->max_sessions = max_sessions;
    client_port->active_sessions = 0;

    return std::make_pair(std::move(server_port), std::move(client_port));
}

} // namespace Kernel
