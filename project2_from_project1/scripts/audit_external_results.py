"""Verify the frozen external evaluation without publishing clinical text.

Reads local ignored artifacts and emits only hashes, counts, and aggregate metrics.
It does not train models or score predictions again; use
``run_external_evaluation --resume-frozen-predictions`` for that check.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from project2_from_project1.src.run_manifest import sha256_file


EXPECTED_F1 = {
    "dictionary+rules": (0.1373, 0.0458, 0.0578),
    "dictionary+knn": (0.1373, 0.0601, 0.0724),
    "crf+rules": (0.2415, 0.1078, 0.0941),
    "crf+knn": (0.2415, 0.1123, 0.1153),
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _verified_hash(path: Path, expected: str) -> None:
    if not path.is_file() or sha256_file(path) != expected:
        raise ValueError(f"missing or changed artifact: {path}")


def _verify_artifacts(directory: Path, hashes: dict[str, str]) -> None:
    root = directory.resolve()
    for name, digest in hashes.items():
        path = (directory / name).resolve()
        if not path.is_relative_to(root):
            raise ValueError("manifest artifact escapes its directory")
        _verified_hash(path, digest)


def _documents(path: Path) -> dict[str, str]:
    output = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        document_id, clinical_text = row["document_id"], row["text"]
        if document_id in output:
            raise ValueError("duplicate document ID")
        output[document_id] = clinical_text
    return output


def audit(project: Path) -> dict:
    artifacts = project / "artifacts"
    models = artifacts / "external-final-models-v1"
    snapshot = artifacts / "external-final-snapshot-v1"
    evaluation = artifacts / "external-final-evaluation-v1"
    development = artifacts / "development-source-reconciled-v1"
    partitions = artifacts / "first-milestone-reconciled-v1" / "frozen-dataset"
    gold = artifacts / "external-multicare-fresh-gold-through70-eligible-v3" / "provisional-gold.jsonl"

    model_manifest = _json(models / "manifest.json")
    snapshot_manifest = _json(snapshot / "manifest.json")
    evaluation_manifest = _json(evaluation / "manifest.json")
    predictions_manifest = _json(evaluation / "predictions-manifest.json")
    partition_manifest = _json(partitions / "manifest.json")
    report = _json(evaluation / "report.json")

    if model_manifest["status"] != "models_frozen_before_external_annotation_access":
        raise ValueError("models were not marked frozen before external annotation")
    if evaluation_manifest["status"] != "completed":
        raise ValueError("external evaluation is incomplete")
    _verify_artifacts(models, model_manifest["artifact_sha256"])
    _verify_artifacts(project, model_manifest["code_sha256"])
    _verify_artifacts(evaluation, evaluation_manifest["artifact_sha256"])
    _verify_artifacts(evaluation, predictions_manifest["prediction_sha256"])
    _verify_artifacts(partitions, partition_manifest["artifact_hashes"])

    model_inputs = model_manifest["input_sha256"]
    _verified_hash(development / "corpus.jsonl", model_inputs["corpus_jsonl_sha256"])
    _verified_hash(development / "gold" / "gold-projection.jsonl", model_inputs["gold_projection_jsonl_sha256"])
    _verified_hash(development / "gold" / "manifest.json", model_inputs["gold_projection_manifest_sha256"])
    _verified_hash(partitions / "manifest.json", model_inputs["partition_manifest_sha256"])
    _verified_hash(snapshot / "raw.jsonl", snapshot_manifest["raw_sha256"])
    _verified_hash(snapshot / "raw.jsonl", evaluation_manifest["input_sha256"]["raw"])
    _verified_hash(gold, evaluation_manifest["input_sha256"]["gold"])
    _verified_hash(models / "manifest.json", evaluation_manifest["input_sha256"]["models_manifest"])
    _verified_hash(models / "manifest.json", predictions_manifest["models_manifest_sha256"])
    _verified_hash(snapshot / "raw.jsonl", predictions_manifest["raw_sha256"])

    split = partition_manifest["partitions"]
    test_ids = set(split["test_document_ids"])
    folds = split["folds"]
    validation = [set(fold["validation_document_ids"]) for fold in folds]
    development_ids = set().union(*validation)
    if len(test_ids) != 11 or len(development_ids) != 42 or len(folds) != 5:
        raise ValueError("unexpected partition sizes")
    if sum(map(len, validation)) != len(development_ids) or development_ids & test_ids:
        raise ValueError("validation folds or test partition overlap")
    if set(model_manifest["training_document_ids"]) != development_ids:
        raise ValueError("models were not trained on the development documents")
    for fold, validation_ids in zip(folds, validation):
        train_ids = set(fold["train_document_ids"])
        if train_ids & validation_ids or train_ids | validation_ids != development_ids:
            raise ValueError("invalid development fold")

    raw_documents = _documents(snapshot / "raw.jsonl")
    gold_documents = _documents(gold)
    if len(raw_documents) != 63 or raw_documents.keys() - gold_documents.keys():
        raise ValueError("snapshot or gold document count changed")
    if any(gold_documents[key] != value for key, value in raw_documents.items()):
        raise ValueError("gold and raw text differ")
    if raw_documents.keys() & (development_ids | test_ids):
        raise ValueError("external snapshot overlaps MCRC partitions")
    if report["documents"] != len(raw_documents) or report["gold_records_excluded_from_snapshot"] != 7:
        raise ValueError("report population differs from the frozen snapshot")
    if not report["resumed_frozen_predictions"]:
        raise ValueError("report does not identify frozen prediction scoring")

    metrics = {}
    for arm, expected in EXPECTED_F1.items():
        result = report["arms"][arm]
        actual = (
            result["entities"]["strict"]["macro_f1"],
            result["relations"]["macro_f1"],
            result["graph"]["concept_edges"]["micro"]["f1"],
        )
        if tuple(round(value, 4) for value in actual) != expected:
            raise ValueError(f"published F1 does not match report for {arm}")
        metrics[arm] = {
            **dict(zip(("entity_macro_f1", "relation_macro_f1", "concept_edge_micro_f1"), actual)),
            "entity_micro": {key: result["entities"]["strict"]["micro"][key]
                             for key in ("precision", "recall", "f1")},
            "relation_micro": {key: result["relations"]["micro"][key]
                               for key in ("precision", "recall", "f1")},
            "concept_edge_micro": {key: result["graph"]["concept_edges"]["micro"][key]
                                   for key in ("precision", "recall", "f1")},
        }
    if report["arms"]["crf+knn"]["crf_converged"] is not False:
        raise ValueError("CRF convergence status changed")
    if report["arms"]["crf+knn"]["relations"]["per_label"]["CAUSES"]["support"] != 9:
        raise ValueError("CAUSES support changed")

    return {
        "status": "verified_local_frozen_evaluation",
        "documents": len(raw_documents),
        "development_documents": len(development_ids),
        "held_out_mcrc_documents": len(test_ids),
        "development_folds": len(folds),
        "verified_model_artifacts": len(model_manifest["artifact_sha256"]),
        "verified_model_code_files": len(model_manifest["code_sha256"]),
        "verified_evaluation_artifacts": len(evaluation_manifest["artifact_sha256"]),
        "metrics": metrics,
        "crf_converged": False,
        "causes_support": 9,
        "snapshot_status": snapshot_manifest["status"],
        "report_sha256": sha256_file(evaluation / "report.json"),
        "models_manifest_sha256": sha256_file(models / "manifest.json"),
        "external_raw_sha256": sha256_file(snapshot / "raw.jsonl"),
        "limitations": [
            "Local artifact verification; clinical inputs and predictions are not in public Git.",
            "The 63-document snapshot did not meet the original 100-document or 20-CAUSES thresholds.",
            "The CRF produced finite output but did not converge within 250 iterations.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="Optional text-only JSON evidence file")
    args = parser.parse_args()
    evidence = audit(args.project)
    rendered = json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
