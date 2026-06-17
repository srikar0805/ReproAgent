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
