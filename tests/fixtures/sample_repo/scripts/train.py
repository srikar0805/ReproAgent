import argparse

from torchvision.datasets import CIFAR10


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.parse_args()
    CIFAR10(root="./data", download=True)


if __name__ == "__main__":
    main()
