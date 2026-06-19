# Security

ReproAgent treats research repositories as untrusted code.

MVP 0.1 is intentionally static: it audits files, commands, dependencies, and missing artifacts without running experiment code. This lets the tool produce useful blocked/runnable verdicts before crossing into execution risk.

Version `0.2.0` adds environment and smoke-test planning, but generation of a Dockerfile or command does not authorize execution.

The execution milestone must satisfy these requirements:

- Run repository commands only inside Docker.
- Use a non-root container user.
- Never mount the host Docker socket.
- Never mount SSH keys, cloud credentials, or user home directories.
- Require approval before enabling network access.
- Display commands before execution.
- Apply CPU, memory, process, and timeout limits.
- Restrict output to a dedicated artifact directory.
- Keep a complete command and patch audit log.
- Stop after a fixed number of repair attempts.

Generated environment plans additionally require:

- Network disabled by default at runtime
- Read-only root filesystem
- All Linux capabilities dropped
- `no-new-privileges`
- CPU, memory, and PID limits
- No home-directory mount
- Only the dedicated artifact directory mounted writable

Milestone 1 performs static inspection only. It does not execute repository code.
