# ReproAgent

ReproAgent is an open-source reproducibility auditor for research papers and their public code/materials.

Its first job is not to promise that every paper can be reproduced. Its job is to produce an evidence-backed verdict:

> Given a paper and its public materials, can the reported result be reproduced from what is actually available?

A blocked result is useful. It tells researchers, reviewers, authors, and labs exactly which scientific artifacts are missing or which documented commands are invalid.

Version `0.1` focuses on static reproducibility auditing:

- Inspect a paper PDF or extracted text file.
- Inspect a Python/PyTorch repository.
- Identify a target result and reported metric.
- Validate README commands against script arguments.
- Discover required datasets, labels, splits, checkpoints, configs, and output files.
- Compare required artifacts against public repository contents.
- Produce a blocked/runnable verdict without executing untrusted code.

## Quick Start

```bash
python -m repro_agent.cli audit \
  --paper ./paper.pdf \
  --repo ./some-local-repo \
  --target "Table 2, Model A, CIFAR-10 accuracy" \
  --output-dir artifacts/my-audit
```

Audit output:

```text
artifacts/my-audit/
  reproduction.yaml
  artifact-audit.json
  command-audit.json
  environment-audit.json
  audit.json
  reproducibility-report.md
```

The lower-level inspection commands are still available:

```bash
repro-agent inspect-paper ./paper.pdf
repro-agent inspect-repo ./some-local-repo
repro-agent init-reproduction \
  --paper ./paper.pdf \
  --repo ./some-local-repo \
  --target "Table 2 accuracy"
```

Remote public repositories can be audited with an explicit temporary clone:

```bash
repro-agent audit \
  --paper ./paper.pdf \
  --repo https://github.com/author/project \
  --target "Table 1 headline result" \
  --clone \
  --output-dir artifacts/project-audit
```

## Current Scope

Supported in the first scaffold:

- Python repositories
- PyTorch-oriented dependency detection
- `requirements.txt`, Conda YAML, and `pyproject.toml`
- Classification and regression metrics such as accuracy, F1, loss, MAE, MAPE, RMSE, and R2
- Static command validation for `argparse` scripts
- Required artifact detection from command arguments
- Missing artifact classification for datasets, labels, splits, checkpoints, configs, and output paths
- Markdown/JSON-style inspection output
- `reproduction.yaml` and reproducibility audit generation

Current statuses:

```text
not_analyzed
inspected
blocked
environment_failed
execution_failed
partially_reproduced
approximately_reproduced
exactly_reproduced
```

Still intentionally out of scope:

- Automatic full experiment execution
- Running untrusted code outside Docker
- Distributed training
- Private datasets
- Automatic acquisition of restricted datasets
- Long-running training
- Scientific changes to model architecture, data, loss, or metrics

## Example Verdict

```text
Status: blocked

Primary blockers:
- data/dataset.h5 unavailable
- data/label.h5 unavailable
- data/split.json unavailable
- fold checkpoints unavailable

Documentation issue:
- README command omits required --output argument

Final verdict:
Reproducible from public materials: false
Primary reason: Required scientific artifacts are unavailable.
```

## Project Layout

```text
repro_agent/
  agents/       Paper, repository, and artifact audit agents
  schemas/      Typed reproduction and audit data structures
  tools/        PDF, git, dependency, command, artifact, and metric helpers
  reporting/    Markdown report generation
  sandbox/      Execution policy placeholders for later Docker stages
```

## Security Direction

ReproAgent `0.1` performs static auditing only. Later execution stages will run third-party repositories only inside Docker. The sandbox design requires explicit command approval, bounded retries, resource limits, no host Docker socket mounts, and artifact-only write access.
