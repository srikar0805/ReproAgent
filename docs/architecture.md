# Architecture

ReproAgent is organized as a CLI-driven reproducibility-audit pipeline around specialized agents.

```text
CLI
  -> Orchestrator
      -> PaperAnalyzer
      -> RepositoryInspector
      -> ArtifactAuditor
      -> EnvironmentBuilder
      -> ExecutionAgent
      -> RepairAgent
      -> ResultVerifier
```

MVP 0.1 implements paper/repository inspection, static command validation, artifact completeness auditing, and a blocked/runnable verdict. Later milestones add Docker builds, smoke tests, repair loops, metric extraction, and full reproduction reports.

The next product layer derives researcher plans from the audit:

```text
Audit evidence
  -> BaselinePlan
  -> ComparisonPlan
```

`BaselinePlan` records exact-reproduction blockers, independent-replication assumptions, and fair-benchmark alternatives.

`ComparisonPlan` records baseline/candidate evaluation entrypoints and the shared dataset, split, preprocessing, metric, fold, and seed requirements needed for a fair comparison.

## Environment Boundary

`EnvironmentBuilder` generates a Dockerfile and build plan from the inspected Python/dependency metadata.

`SandboxExecutor` generates a hardened `docker run` prefix and progressive smoke-test stages. It does not execute containers by itself.

```text
Static audit
  -> environment plan
  -> Docker build
  -> imports
  -> CLI help
  -> configuration
  -> dataset loader
  -> checkpoint loading
  -> one-batch inference
  -> short experiment
  -> full experiment
```

Each stage after static configuration requires explicit approval when it touches data, checkpoints, or experiment execution.

## Stable Contracts

Machine-readable outputs are checked against bundled JSON Schemas before writing. The current schema version is `0.2.0`.

## Pipeline

```text
Paper + repository
  -> experiment identification
  -> artifact completeness audit
  -> environment dependency summary
  -> command validation
  -> reproducibility report
```

## Agent Contracts

`PaperAnalyzer` extracts target metrics, datasets, models, hyperparameters, and uncertainties.

`RepositoryInspector` detects dependency files, framework, config files, candidate commands, dataset hints, and Git metadata.

`ArtifactAuditor` compares required command artifacts with the repository inventory and classifies missing datasets, labels, splits, checkpoints, configs, and output paths.

`Orchestrator` combines those outputs into `reproduction.yaml`, `artifact-audit.json`, `command-audit.json`, `environment-audit.json`, and `reproducibility-report.md`.
