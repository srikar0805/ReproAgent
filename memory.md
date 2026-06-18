# ReproAgent Memory

This file is the project handoff log. It records what we built, what we learned, what failed, and what should happen next.

## Product Direction

ReproAgent started as a "Research Reproduction Agent" idea: give it a paper and repository, have it build an environment, run the experiment, repair issues, compare metrics, and produce a report.

The stronger product direction emerged after testing against a real paper/repo:

> ReproAgent is a static, evidence-backed reproducibility auditor that inspects a paper and repository, validates documented commands, identifies required scientific artifacts, and determines whether the selected result is runnable, blocked, or ambiguous without executing untrusted research code.

Important principle:

> A blocked result is not a failed product run. It is a scientifically useful finding.

The first public MVP should be **ReproAgent v0.1 — Static Reproducibility Auditor**.

## Current Repository

GitHub remote:

```text
https://github.com/srikar0805/ReproAgent.git
```

Main branch:

```text
main
```

Known commits:

```text
2161ef9 Initial ReproAgent scaffold
c1727de Add evidence-backed artifact audit
430e156 Add project memory handoff
```

## Current MVP Scope

MVP 0.1 performs static auditing only. It does not execute untrusted repository code.

Supported:

- Python repositories
- PyTorch-oriented repository inspection
- PDF or extracted text paper input
- `requirements.txt`, Conda environment files, and `pyproject.toml`
- Classification and regression metric detection
- Static README command extraction
- Static `argparse` command validation
- Required artifact detection from command arguments
- Evidence-backed missing artifact reporting
- Dataset, label, split, checkpoint, config, and output-path classification
- JSON, YAML, and Markdown audit outputs
- Blocked/runnable verdicts

Intentionally out of scope for MVP 0.1:

- Full experiment execution
- Docker environment building
- Automated repairs
- Metric verification from executed runs
- Private dataset access
- Long-running training
- Scientific changes to model architecture, data, loss, metrics, or splits

## CLI Commands

Primary command:

```bash
python -m repro_agent.cli audit \
  --paper ./paper.pdf \
  --repo ./some-local-repo \
  --target "Table 2, Model A, CIFAR-10 accuracy" \
  --output-dir artifacts/my-audit
```

Remote repositories require explicit temporary clone:

```bash
repro-agent audit \
  --paper ./paper.pdf \
  --repo https://github.com/author/project \
  --target "Table 1 headline result" \
  --clone \
  --output-dir artifacts/project-audit
```

Lower-level commands:

```bash
python -m repro_agent.cli inspect-paper ./paper.pdf
python -m repro_agent.cli inspect-repo ./some-local-repo
python -m repro_agent.cli init-reproduction \
  --paper ./paper.pdf \
  --repo ./some-local-repo \
  --target "Table 2 accuracy"
```

Audit outputs:

```text
reproduction.yaml
artifact-audit.json
command-audit.json
environment-audit.json
audit.json
reproducibility-report.md
```

Research workflow planning:

```bash
repro-agent baseline \
  --paper paper.pdf \
  --repo ./baseline \
  --target "Table 1 overall MAE" \
  --mode exact_reproduction \
  --output-dir experiments/baseline

repro-agent compare \
  --paper paper.pdf \
  --baseline-repo ./baseline \
  --candidate-repo ./candidate \
  --dataset ./data \
  --target "Table 1 overall MAE" \
  --mode fair_benchmark \
  --output-dir experiments/comparison
```

These commands generate plans only. They do not execute repository code.

## Architecture

Implemented components:

- `PaperAnalyzer`: extracts title, target, datasets, metrics, hyperparameters, and uncertainties.
- `RepositoryInspector`: detects framework, dependency files, entrypoints, configs, dataset hints, README command, and Git metadata.
- `ArtifactAuditor`: compares required artifacts with repository inventory and classifies blockers.
- `Orchestrator`: connects analyzers and writes audit contracts.
- `report_builder`: generates Markdown reports.
- `command_validator`: validates README commands against static `argparse` definitions.
- `artifact_discovery`: inventories files, external links, artifact requirements, missing artifacts, and code-line evidence.
- `BaselinePlan`: converts audit blockers into exact-reproduction, independent-replication, and fair-benchmark paths.
- `ComparisonPlan`: defines the shared protocol required to compare a baseline and candidate fairly.

Future placeholder components:

- `EnvironmentBuilder`
- `ExecutionAgent`
- `RepairAgent`
- `ResultVerifier`
- `SandboxExecutor`

## Status Model

Public audit verdicts:

```text
runnable
blocked
ambiguous
inspection_failed
restricted
cost_prohibitive
```

`runnable` means the static audit did not find blocking missing artifacts. It does not mean the result has been reproduced.

Internal execution/reproduction states:

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

Important meanings:

- `blocked`: experiment cannot legitimately begin because required external scientific artifacts are missing.
- `environment_failed`: materials exist, but dependencies/system environment cannot be reconstructed.
- `execution_failed`: environment builds, but the official command fails.
- `partially_reproduced`: meaningful portion runs, but original scientific setup cannot be matched exactly.
- `approximately_reproduced`: correct experiment runs and metric is within tolerance.
- `exactly_reproduced`: correct setup runs and matches strict tolerance.

## Evidence Engine

The most important implementation upgrade so far is evidence-backed artifact reporting.

Missing artifacts now include:

- stable finding ID
- confidence
- artifact name
- path
- category
- severity
- required purpose
- structured evidence
- searched locations
- impact on execution and verification

Example shape:

```yaml
artifact:
  name: dataset.h5
  category: dataset
  status: missing
  required_for: training_and_evaluation
evidence:
  - source: README.md
    kind: command_argument
    detail: "--dataset data/dataset.h5"
  - source: evaluate_ensemble.py
    line: 70
    operation: file access
searched_locations:
  - repository
  - git_lfs
  - github_releases
  - linked_downloads
impact:
  blocks_execution: true
  blocks_result_verification: true
confidence: 0.9
```

This distinction matters: ReproAgent should not merely say "missing file"; it should explain why the file is required and where that conclusion came from.

## Pigformer Test Case

Paper:

```text
/Users/srikarreddy/Downloads/2606.05611v1.pdf
```

Repository:

```text
https://github.com/iambashar/Pigformer
```

Temporary local checkout used during development:

```text
/private/tmp/Pigformer
```

Target:

```text
Table 1 PigFormer MaskDINO overall MAE 3.87 mm
```

Command identified from README:

```bash
python evaluate_ensemble.py \
  --checkpoints results/fold0/best.pt results/fold1/best.pt results/fold2/best.pt results/fold3/best.pt \
  --dataset data/dataset.h5 \
  --labels data/label.h5 \
  --split_json data/split.json \
  --aggregation output
```

Static command validation found a documentation issue:

```text
README command omits required argument --output.
```

Corrected structural command:

```bash
python evaluate_ensemble.py \
  --checkpoints results/fold0/best.pt results/fold1/best.pt results/fold2/best.pt results/fold3/best.pt \
  --dataset data/dataset.h5 \
  --labels data/label.h5 \
  --split_json data/split.json \
  --aggregation output \
  --output artifacts/metrics.json
```

Required missing artifacts:

```text
results/fold0/best.pt
results/fold1/best.pt
results/fold2/best.pt
results/fold3/best.pt
data/dataset.h5
data/label.h5
data/split.json
```

Verdict:

```text
blocked
```

Primary reason:

```text
Required scientific artifacts are unavailable.
```

Why this was useful:

- It proved the project should audit reproducibility before attempting execution.
- It showed that "code available" does not mean "reproducible from public materials."
- It exposed a README command defect.
- It gave a realistic first acceptance test for artifact completeness.

## Problems We Faced

1. Initial project shape was too execution-focused.
   We reframed MVP 0.1 around auditing and verdicts.

2. Paper parsing is messy.
   Early metric extraction picked up related-work "accuracy" instead of the paper's `3.87 mm overall MAE`. Regression metric support was added for MAE/MAPE/RMSE/R2.

3. README commands can be incomplete.
   Pigformer omitted required `--output`. Static `argparse` validation now detects that.

4. README command extraction needed multiline support.
   Pigformer uses multiline shell commands. The parser now joins continuations and skips setup commands.

5. Public repos often omit scientific artifacts.
   Pigformer omits HDF5 data, labels, split definitions, and fold checkpoints. ReproAgent now classifies this as `blocked`.

6. Missing dependency error appeared during manual execution.
   User hit `ModuleNotFoundError: No module named 'torch'`. Installing the repo dependencies resolves that class of error, but Pigformer still cannot run without data/checkpoints.

7. Running the command from the wrong directory caused confusion.
   `evaluate_ensemble.py` lives in the Pigformer repo, not in the ReproAgent repo or workspace root.

8. Directly typing file paths in zsh caused "no such file or directory".
   Those paths are command inputs, not shell commands.

9. Generated reports needed evidence, not just file names.
   The evidence engine now records README arguments and Python file-access lines.

10. Static audit alone did not complete the researcher's daily workflow.
    Baseline and compare planning were added as the first step toward runnable experiments.

11. A training command was initially treated as sufficient for candidate comparison.
    Comparison planning now requires a candidate evaluation entrypoint.

12. Nested non-git fixture directories inherited the parent repository remote.
    Git metadata detection now requires the inspected directory to be the actual Git root.

## Security Decisions

MVP 0.1 must not execute repository code.

Future execution must use Docker isolation:

- non-root containers
- no host Docker socket
- no SSH keys or cloud credentials
- explicit network approval
- CPU, memory, process, and timeout limits
- dedicated artifact-only output directories
- complete command and patch logs
- bounded repair attempts

Operational fixes may be automatic and recorded:

- add missing output argument
- create output directory
- pin dependency
- fix equivalent removed API
- correct obvious relative path

Scientific repairs must require explicit approval and may disqualify exact reproduction:

- change architecture
- change dataset
- generate replacement split
- substitute checkpoints
- change optimizer
- change loss
- change metric
- reduce final epochs
- change ensemble logic

## Tests And Verification

`pytest` was not installed locally during development, so tests were verified by direct invocation of test functions plus `compileall`.

Commands used:

```bash
python -m compileall repro_agent tests
python -m repro_agent.cli audit --help
```

CI was added with GitHub Actions and pytest coverage configuration. Locally, `pytest` may still need to be installed with:

```bash
python -m pip install -e ".[dev]"
```

Manual assertion suite invoked tests from:

```text
tests/unit/test_paper_analyzer.py
tests/unit/test_repository_inspector.py
tests/unit/test_orchestrator.py
tests/unit/test_metric_extractor.py
tests/unit/test_artifact_auditor.py
```

Pigformer audit command used:

```bash
python -m repro_agent.cli audit \
  --paper /Users/srikarreddy/Downloads/2606.05611v1.pdf \
  --repo /private/tmp/Pigformer \
  --target "Table 1 PigFormer MaskDINO overall MAE 3.87 mm" \
  --output-dir artifacts/pigformer-audit
```

Expected output:

```text
Status: blocked
Verdict: Required scientific artifacts are unavailable.
```

## Important Files

Core:

```text
repro_agent/cli.py
repro_agent/orchestrator.py
repro_agent/agents/paper_analyzer.py
repro_agent/agents/repository_inspector.py
repro_agent/agents/artifact_auditor.py
repro_agent/tools/artifact_discovery.py
repro_agent/tools/command_validator.py
repro_agent/tools/code_search.py
repro_agent/tools/metric_extractor.py
repro_agent/reporting/report_builder.py
repro_agent/schemas/audit.py
```

Docs:

```text
README.md
docs/architecture.md
docs/security.md
docs/adding-frameworks.md
docs/roadmap.md
```

Generated Pigformer audit:

```text
artifacts/pigformer-audit/
```

Note: `artifacts/` is gitignored by design.

## Next Development Order

Recommended next steps:

1. Make evidence extraction more precise by tracing CLI args through call graphs and dataset helper classes.
2. Add repository-local Git LFS detection and GitHub release inventory.
3. Add external-link classification and restricted-access detection.
4. Add JSON Schema validation for audit, baseline, and comparison outputs.
5. Build an isolated environment reconstruction layer.
6. Add import, CLI help, dataset-loader, and checkpoint smoke tests.
7. Create a proven adapter contract for candidate evaluation.
8. Execute one small baseline and candidate under the same protocol.
9. Extract metrics and generate a statistical comparison report.
10. Add improvement planning only after fair comparison works end to end.

## Benchmark Plan

First benchmark should include multiple outcome classes:

```text
fully reproducible small projects
missing datasets
broken environments
incorrect README commands
missing checkpoints or splits
ambiguous experiment definitions
```

Useful metrics:

```text
artifact detection precision
artifact detection recall
command-validation accuracy
correct blocker classification
environment-build success
false scientific repairs
manual interventions
time to verdict
cost-estimation error
final reproduction success
```

## Current Product Statement

> ReproAgent is a static, evidence-backed reproducibility auditor that inspects a paper and repository, validates documented commands, identifies required scientific artifacts, and determines whether the selected result is runnable, blocked, or ambiguous without executing untrusted research code.
