# Adding Frameworks

Framework support starts in `repro_agent/tools/dependency_tools.py`.

To add a framework:

1. Add dependency or import markers to `FRAMEWORK_MARKERS`.
2. Add repository fixtures that include realistic dependency files and entrypoints.
3. Add command inference rules only when they are stable across projects.
4. Keep framework-specific execution behavior out of the paper and repository analyzers.

The first supported framework target is PyTorch classification.
