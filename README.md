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

## Baseline And Compare Planning

ReproAgent now provides the first planning slice of the researcher workflow:

```text
Audit -> Baseline -> Compare
```

Prepare a baseline:

```bash
repro-agent baseline \
  --paper paper.pdf \
  --repo ./baseline-repo \
  --target "Table 1 overall MAE" \
  --mode exact_reproduction \
  --output-dir experiments/baseline-01
```

Plan a fair comparison:

```bash
repro-agent compare \
  --paper paper.pdf \
  --baseline-repo ./baseline-repo \
  --candidate-repo ./my-model \
  --dataset ./data \
  --target "Table 1 overall MAE" \
  --mode fair_benchmark \
  --output-dir experiments/comparison-01
```

Scientific modes:

```text
exact_reproduction
independent_replication
fair_benchmark
```

- `exact_reproduction` requires the original artifacts and protocol.
- `independent_replication` permits explicit, reviewable assumptions but cannot validate the exact published number.
- `fair_benchmark` defines a new common protocol for baseline and candidate and must not be presented as paper reproduction.

These commands currently generate preparation and comparison plans. They do not execute repository code yet.

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

Public audit verdicts:

```text
runnable
blocked
ambiguous
inspection_failed
restricted
cost_prohibitive
```

Execution/reproduction states:

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

`runnable` means the static audit did not find blocking missing artifacts. It does not mean the result has been reproduced.

Machine-readable audit outputs include report metadata such as schema version, tool version, audit ID, creation time, repository commit, and paper hash.

Still intentionally out of scope:

- Automatic full experiment execution
- Running untrusted code outside Docker
- Distributed training
- Private datasets
- Automatic acquisition of restricted datasets
- Long-running training
- Scientific changes to model architecture, data, loss, or metrics

The next execution milestone will build isolated environments and smoke tests. It will remain separate from static audit/planning.

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

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for product workflow goals, benchmark targets, and what not to build yet.
