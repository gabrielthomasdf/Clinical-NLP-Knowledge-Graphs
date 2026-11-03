"""Mention-level consistency for new relation predictions.

This postprocessor is opt-in so that published academic predictions and their
recorded metrics remain reproducible. It changes a positive HAS_FINDING only
when a positive NEGATES points to the very same Finding prediction ID.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Mapping

from project2_from_project1.src.clinical_documents import CanonicalRelation
from project2_from_project1.src.relation_evaluation import RelationPrediction

VERSION = "negated-finding-consistency-v1"


def enforce_negation_consistency(predictions: Iterable[RelationPrediction]) -> tuple[RelationPrediction, ...]:
    """Keep one decision per candidate while removing contradictory positives."""
    items = tuple(predictions)
    if len({item.pair_key for item in items}) != len(items):
        raise ValueError("duplicate relation prediction pair")
    negated = {
        (item.document_id, item.target_id)
        for item in items
        if item.canonical_label is CanonicalRelation.NEGATES
    }
    result = []
    for item in items:
        if item.canonical_label is CanonicalRelation.HAS_FINDING and (item.document_id, item.target_id) in negated:
            evidence = dict(item.evidence) if isinstance(item.evidence, Mapping) else {"original_evidence": item.evidence}
            evidence["consistency"] = {"version": VERSION, "original_label": item.canonical_label.value}
            result.append(replace(item, native_label=CanonicalRelation.NO_RELATION.value,
                                  canonical_label=CanonicalRelation.NO_RELATION,
                                  method=f"{item.method}+{VERSION}", model_version=f"{item.model_version}+{VERSION}",
                                  evidence=evidence, neighbor_vote_fraction=None))
        else:
            result.append(item)
    return tuple(result)


def count_negation_conflicts(predictions: Iterable[RelationPrediction]) -> int:
    items = tuple(predictions)
    negated = {(item.document_id, item.target_id) for item in items if item.canonical_label is CanonicalRelation.NEGATES}
    return sum(item.canonical_label is CanonicalRelation.HAS_FINDING and
               (item.document_id, item.target_id) in negated for item in items)
