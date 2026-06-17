FROM python:3.11-slim

RUN useradd --create-home --uid 1000 repro
WORKDIR /workspace

COPY pyproject.toml README.md ./
COPY repro_agent ./repro_agent
RUN pip install --no-cache-dir .

USER repro
ENTRYPOINT ["repro-agent"]
