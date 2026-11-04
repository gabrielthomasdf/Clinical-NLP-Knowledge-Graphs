"""Verify the public development-CV evidence against local study artifacts.

The command prints only aggregate counts, hashes, and status. It never prints
corpus text, annotations, predictions, or document identifiers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY = Path(__file__).resolve().parents[2]
DEFAULT_STUDY = REPOSITORY / "project2_from_project1" / "artifacts" / "study-portfolio-consolidated-v1"
DEFAULT_EVIDENCE = REPOSITORY / "project2_from_project1" / "docs" / "development-cv-results-evidence.json"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def audit(study: Path, evidence_path: Path) -> dict[str, Any]:
    evidence = _read(evidence_path)
    root = _read(study / "manifest.json")
    entities = _read(study / "entities" / "summary.json")
    relations = _read(study / "relations" / "summary.json")
    graph = _read(study / "graph" / "summary.json")

    _expect(evidence["status"] == "verified_local_nested_development_evaluation", "unexpected evidence status")
    _expect(root["git"]["commit"] == evidence["code_commit"], "code commit differs from evidence")
    _expect(root["test_partition_read"] is False, "held-out test partition was marked as read")
    _expect(root["configuration"] == evidence["configuration"], "study configuration differs from evidence")
    _expect(root["inputs"] == evidence["inputs"], "input hashes differ from evidence")

    summary_paths = {
        "root_manifest": study / "manifest.json",
        "entity_summary": study / "entities" / "summary.json",
        "relation_summary": study / "relations" / "summary.json",
        "graph_summary": study / "graph" / "summary.json",
    }
    for name, path in summary_paths.items():
        _expect(_sha256(path) == evidence["artifact_hashes"][name], f"{name} hash differs from evidence")

    verified_artifacts = 0
    for relative, expected in root["artifact_hashes"].items():
        path = study / relative
        _expect(path.is_file(), f"missing declared artifact: {relative}")
        _expect(_sha256(path) == expected, f"declared artifact hash differs: {relative}")
        verified_artifacts += 1

    for tag, expected in evidence["crf_outer_runs"].items():
        selection = _read(study / "entities" / "crf" / tag / "selection.json")
        manifest_path = study / "entities" / "crf" / tag / "outer" / "manifest.json"
        manifest = _read(manifest_path)
        observed = {
            "selected_l2": selection["selected_l2"],
            "status": manifest["status"],
            "converged": manifest["converged"],
            "iterations": manifest["training"]["iterations"],
            "manifest_sha256": _sha256(manifest_path),
        }
        _expect(observed == expected, f"CRF outer run differs from evidence: {tag}")

    for arm, expected in evidence["metrics"].items():
        recognizer = "canonical-dictionary" if arm.startswith("dictionary") else "semi-markov-crf"
        observed = {
            "entity_macro_f1": entities["arms"][recognizer]["aggregate"]["macro_f1"],
            "entity_micro_f1": entities["arms"][recognizer]["aggregate"]["micro_f1"],
            "relation_macro_f1": relations["arms"][arm]["across_folds"]["macro_f1"],
            "relation_micro_f1": relations["arms"][arm]["across_folds"]["micro_f1"],
            "concept_edge_f1": graph["arms"][arm]["concept_edge_f1"],
            "concept_edge_pooled": graph["arms"][arm]["pooled"]["concept_edges"],
        }
        _expect(observed == expected, f"aggregate metrics differ from evidence: {arm}")

    observed_ceilings = {
        arm: relations["arms"][arm]["across_folds"]["macro_f1"]
        for arm in ("gold+rules", "gold+knn")
    }
    _expect(observed_ceilings == evidence["diagnostic_relation_ceilings"],
            "diagnostic ceiling metrics differ from evidence")

    return {
        "code_commit": evidence["code_commit"],
        "folds": len(evidence["crf_outer_runs"]),
        "held_out_test_partition_read": False,
        "status": "verified",
        "verified_artifacts": verified_artifacts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=DEFAULT_STUDY)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    arguments = parser.parse_args()
    print(json.dumps(audit(arguments.study, arguments.evidence), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
