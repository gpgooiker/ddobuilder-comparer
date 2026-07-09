import argparse
import logging

import pandas as pd

import ddo_stats as stats


def load_ddo_file(file_path: str) -> list[str]:
    ddo_file_from_pandas = pd.read_fwf(file_path, colspecs=[(0, 999)], header=None)
    ddo_file_in_numpy = ddo_file_from_pandas.to_numpy()

    return [str(row[0]) for row in ddo_file_in_numpy]


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug helper for ddo_stats.py")
    parser.add_argument(
        "file_path",
        nargs="?",
        default="ddo_files_from_maetrim_builder/paste_your_export_here.txt",
        help="Path to a DDOBuilder export text file.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s", force=True)

    ddo_file = load_ddo_file(args.file_path)

    offensive_fitness_score = stats.compute_offensive_score(ddo_file)
    defensive_fitness_score = stats.compute_defensive_score(ddo_file)

    print(f"Offensive fitness score: {offensive_fitness_score:.2f}")
    print(f"Defensive fitness score: {defensive_fitness_score:.2f}")


if __name__ == "__main__":
    main()