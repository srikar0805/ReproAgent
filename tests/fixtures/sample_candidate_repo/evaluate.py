import argparse

import torch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.parse_args()
    print(torch.__version__)


if __name__ == "__main__":
    main()
