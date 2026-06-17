# Security

ReproAgent treats research repositories as untrusted code.

MVP 0.1 is intentionally static: it audits files, commands, dependencies, and missing artifacts without running experiment code. This lets the tool produce useful blocked/runnable verdicts before crossing into execution risk.

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

Milestone 1 performs static inspection only. It does not execute repository code.
