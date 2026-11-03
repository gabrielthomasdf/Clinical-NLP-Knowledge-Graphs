"""Run the public synthetic demonstration with portfolio-friendly defaults."""

from __future__ import annotations

import argparse
from pathlib import Path

from project2_from_project1.src.study_pipeline import run_full_study
from project2_from_project1.src.synthetic_fixture import make_synthetic_workspace


END_TO_END_ARMS = (
    "dictionary+rules",
    "dictionary+knn",
    "crf+rules",
    "crf+knn",
)


def run_demo(output_root: str | Path, *, max_iterations: int = 20) -> tuple[Path, dict]:
    """Generate deterministic fictional input and execute every study arm."""
    root = Path(output_root)
    workspace = make_synthetic_workspace(root / "input")
    output = root / "output"
    manifest = run_full_study(
        workspace.corpus_jsonl,
        workspace.adjudication_jsonl,
        workspace.frozen_dataset,
        output,
        max_iterations=max_iterations,
    )
    return output, manifest


def _metric(value: dict | None) -> str:
    return "n/a" if value is None else f"{value['mean']:.4f}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        default="project2_from_project1/artifacts/portfolio-demo",
        help="Directory for generated fictional input and outputs",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=20,
        help="Maximum CRF iterations; 20 is the documented quick demonstration",
    )
    arguments = parser.parse_args()
    if arguments.max_iterations < 1:
        parser.error("--max-iterations must be at least 1")

    output, manifest = run_demo(arguments.output_root, max_iterations=arguments.max_iterations)

    print("\nSynthetic demonstration completed")
    print(f"Fictional documents: {Path(arguments.output_root) / 'input' / 'corpus.jsonl'}")
    print(f"Manifest: {output / 'manifest.json'}")
    print(f"Knowledge graphs: {output / 'graph'}")
    print("\nEnd-to-end results on synthetic data (integration check only):")
    print("approach                 entity F1   relation F1   graph edge F1   failed folds")
    for arm in END_TO_END_ARMS:
        result = manifest["arms"][arm]
        failed = ",".join(map(str, result["failed_folds"])) or "none"
        print(
            f"{arm:<24} {_metric(result['entity_macro_f1']):>9}"
            f" {_metric(result['relation_macro_f1']):>13}"
            f" {_metric(result['concept_edge_f1']):>15}   {failed}"
        )


if __name__ == "__main__":
    main()
