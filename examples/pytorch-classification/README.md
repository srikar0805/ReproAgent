# PyTorch Classification Example

This folder is reserved for the first full reproduction demo.

The intended flow:

```bash
repro-agent init-reproduction \
  --paper ./paper.pdf \
  --repo https://github.com/author/project \
  --target "Table 2, Model A, CIFAR-10 accuracy" \
  --device cuda
```

The generated `reproduction.yaml` becomes the handoff into Docker-based smoke testing.
