"""Compare frozen relation predictions before and after negation consistency.

This experiment does not retrain or touch held-out labels. Its endpoint is the
number of contradictory mention-level decisions, not a clinical quality metric.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from project2_from_project1.src.clinical_documents import load_jsonl
from project2_from_project1.src.relation_consistency import VERSION, count_negation_conflicts, enforce_negation_consistency
from project2_from_project1.src.relation_evaluation import load_relation_predictions, write_relation_predictions
from project2_from_project1.src.supervised_contracts import load_contract_jsonl, write_contract_jsonl
from project2_from_project1.src.supervised_graph import build_predicted_graph, evaluate_graph


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(study_output: Path, output: Path, corpus: Path | None = None) -> dict:
    if output.resolve().is_relative_to(study_output.resolve()):
        raise ValueError("output must be outside the input study directory")
    rows = []
    texts = {item.document_id: item.text for item in load_jsonl(corpus)} if corpus is not None else None
    for recognizer in ("dictionary", "crf"):
        for classifier in ("rules", "knn"):
            for fold in (1, 2):
                if classifier == "rules":
                    source = study_output / "relations" / classifier / recognizer / f"fold-{fold:02d}" / "predictions.jsonl"
                else:
                    source = study_output / "relations" / classifier / f"fold-{fold:02d}" / recognizer / "predictions.jsonl"
                predictions = load_relation_predictions(source)
                corrected = enforce_negation_consistency(predictions)
                target = output / classifier / recognizer / f"fold-{fold:02d}" / "predictions.jsonl"
                write_relation_predictions(corrected, target)
                before = count_negation_conflicts(predictions)
                after = count_negation_conflicts(corrected)
                row = {"arm": f"{recognizer}+{classifier}", "fold": fold,
                             "predictions": len(predictions), "conflicts_before": before,
                             "conflicts_after": after, "changed_decisions": sum(a != b for a, b in zip(predictions, corrected)),
                             "source_sha256": _sha256(source), "corrected_sha256": _sha256(target)}
                if texts is not None:
                    graph_dir = study_output / "graph"
                    original = load_contract_jsonl(graph_dir / f"{recognizer}-{classifier}" / f"fold-{fold:02d}" / "graph.jsonl", "graph")
                    gold = load_contract_jsonl(graph_dir / "gold" / f"fold-{fold:02d}" / "graph.jsonl", "graph")
                    entity_dir = study_output / "entities" / recognizer / f"fold-{fold:02d}"
                    entity_file = entity_dir / ("outer/predictions.jsonl" if recognizer == "crf" else "predictions.jsonl")
                    entities = load_contract_jsonl(entity_file, "entity")
                    document_ids = sorted({item.document_id for item in original})
                    rebuilt_original = build_predicted_graph(texts, document_ids, entities, predictions)
                    if evaluate_graph(gold, rebuilt_original)["concept_edges"]["micro"] != evaluate_graph(gold, original)["concept_edges"]["micro"]:
                        raise ValueError("original graph does not match source predictions")
                    corrected_graph = build_predicted_graph(texts, document_ids, entities, corrected)
                    graph_target = output / "graph" / f"{recognizer}-{classifier}" / f"fold-{fold:02d}" / "graph.jsonl"
                    write_contract_jsonl(corrected_graph, graph_target)
                    before_metrics = evaluate_graph(gold, original)
                    after_metrics = evaluate_graph(gold, corrected_graph)
                    row["concept_edge_micro_before"] = before_metrics["concept_edges"]["micro"]
                    row["concept_edge_micro_after"] = after_metrics["concept_edges"]["micro"]
                    row["corrected_graph_sha256"] = _sha256(graph_target)
                rows.append(row)
    report = {"schema_version": 1, "postprocessor": VERSION,
              "scope": "frozen predictions; data source determined by study output and corpus inputs",
              "metric": "contradictory mention-level NEGATES/HAS_FINDING decisions",
              "rows": rows}
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-output", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, help="Original corpus JSONL, needed for graph F1 comparison")
    args = parser.parse_args()
    report = run(args.study_output, args.output_dir, args.corpus)
    print(json.dumps({"rows": len(report["rows"]),
                      "conflicts_before": sum(row["conflicts_before"] for row in report["rows"]),
                      "conflicts_after": sum(row["conflicts_after"] for row in report["rows"]),
                      "changed_decisions": sum(row["changed_decisions"] for row in report["rows"])}, sort_keys=True))


if __name__ == "__main__":
    main()
