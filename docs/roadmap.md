# Roadmap

ReproAgent should become trustworthy before it becomes broad.

The product succeeds when researchers can trust three things:

1. The verdict is accurate.
2. Every verdict is supported by inspectable evidence.
3. The tool never silently changes the science.

## Product Workflows

Long term, ReproAgent should support five workflows:

```text
AUDIT      Can this published result be reproduced?
PREPARE    Is my own project ready for publication?
REPRODUCE  Can the experiment be safely executed and verified?
REVIEW     What evidence should a reviewer inspect?
WATCH      Is the published artifact still reproducible?
```

Do not build all five immediately. Build them on top of one strong evidence model.

## Researcher Journey

The user-facing product direction is:

```text
Audit
  -> Baseline
  -> Compare
  -> Improve
  -> Publish
```

The current `baseline` and `compare` commands are static planning workflows. They preserve the scientific distinction between:

```text
Exact reproduction
Independent replication
Fair benchmark comparison
```

Execution remains a later security milestone.

## Current Priority

MVP 0.1 remains a static reproducibility auditor. It should not execute repository code.

Immediate quality bar:

- Evidence-backed findings
- Explicit public audit verdicts
- Versioned output metadata
- Stable finding identifiers
- Pytest and CI
- Integration fixtures
- External artifact discovery
- Known limitations documentation

## Public Audit Verdicts

Pre-execution verdicts:

```text
RUNNABLE
BLOCKED
AMBIGUOUS
INSPECTION_FAILED
RESTRICTED
COST_PROHIBITIVE
```

`RUNNABLE` means all known required artifacts are available and the command is structurally valid. It does not mean the result has been reproduced.

Execution states remain separate:

```text
ENVIRONMENT_FAILED
EXECUTION_FAILED
PARTIALLY_REPRODUCED
APPROXIMATELY_REPRODUCED
EXACTLY_REPRODUCED
```

## Evidence Engine Goals

Every conclusion should answer:

```text
What was found?
Why is it required?
Where was it referenced?
Where did ReproAgent search?
How confident is the conclusion?
What does its absence prevent?
```

Near-term improvements:

- Trace command arguments through helper methods.
- Follow dataset-loader classes.
- Resolve constants and path concatenation.
- Detect dynamically generated paths.
- Find dependencies in shell scripts and configuration files.
- Inspect Git LFS pointers.
- Inspect GitHub releases.
- Classify linked artifacts from Zenodo, Hugging Face, Figshare, OSF, Kaggle, Google Drive, and project pages.
- Distinguish unavailable from restricted.
- Record confidence and alternative interpretations.

## Claim-To-Evidence Graph

ReproAgent should eventually connect a paper result to all evidence needed to produce it:

```text
Paper claim
  -> table/figure result
  -> reported metric
  -> evaluation command
  -> script
  -> configuration
  -> dataset, labels, split
  -> checkpoints
  -> metrics output
```

Each edge should preserve source, line/page, extraction type, and confidence.

## Benchmark Plan

Build ReproAgentBench before claiming broad reliability.

Suggested categories:

```text
fully runnable small repositories
missing datasets
missing splits or labels
missing checkpoints
incorrect README commands
broken dependencies
restricted datasets
ambiguous experiment targets
```

Target metrics:

```text
Artifact detection precision        >= 90%
Artifact detection recall           >= 85%
Command validation accuracy         >= 95%
Correct verdict classification      >= 90%
Evidence location accuracy          >= 90%
False runnable verdict rate         < 2%
False scientific repair rate        0%
```

The most dangerous failure is declaring a project runnable when essential scientific materials are absent.

## What Not To Build Yet

Do not prioritize:

- Polished web UI
- Every framework/language
- Autonomous cloud spending
- Full training on large models
- Public paper ranking
- Automatic accusations of flawed research
- Automatic scientific repairs
- General-purpose research chatbot
- Conference integrations before benchmark credibility
- A single unexplained reproducibility score

## V0.2 Baseline And Compare

Minimum target:

- Python and PyTorch
- One classification or regression task
- Local dataset
- Baseline and candidate repositories
- Shared split, preprocessing, and metric
- Isolated environment reconstruction
- Smoke tests before full evaluation
- Markdown and JSON comparison report

Success should be measured by time to first runnable baseline, manual actions required, fair-comparison completion rate, and compute wasted before detecting blockers.

Current `0.2.0` progress:

- Real pytest suite and coverage run locally
- GitHub Actions invokes `python -m pytest`
- Versioned JSON Schema validation
- Dockerfile/environment plan generation
- Hardened runtime command generation
- Progressive smoke-test plan
- Candidate adapter contract

Still missing:

- Docker engine integration
- Actual image build
- Actual smoke-test execution
- Dataset/checkpoint adapters
- Metric extraction from a real run
- End-to-end baseline reproduction
