"""Pure application service for the public interactive demonstration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from project1.paths import VOCAB_DIR
from project1.src.extraction import extract_entities
from project1.src.graph.build import build_case_graph, load_entity_vocabulary


@dataclass(frozen=True)
class DemoAnalysis:
    entities: tuple[dict, ...]
    relations: tuple[dict, ...]
    nodes: tuple[dict, ...]
    edges: tuple[dict, ...]


@lru_cache(maxsize=1)
def demo_vocabulary() -> tuple:
    """Load the versioned Project 1 vocabularies once per process."""
    return tuple(load_entity_vocabulary(VOCAB_DIR))


def analyze_text(text: str, *, case_id: str = "interactive") -> DemoAnalysis:
    """Run dictionary entities, rule relations and graph construction."""
    clean_text = text.strip()
    if not clean_text:
        return DemoAnalysis((), (), (), ())

    vocabulary = list(demo_vocabulary())
    extracted = extract_entities(clean_text, vocabulary)
    nodes, edges = build_case_graph(case_id, clean_text, vocabulary)
    node_by_id = {node.node_id: node for node in nodes}

    entities = tuple(
        {
            "entity": entity.label,
            "type": entity.type,
            "mentions": entity.count,
            "surface_forms": ", ".join(entity.surface_forms),
            "offsets": ", ".join(f"{start}:{end}" for start, end in entity.positions),
        }
        for entity in extracted
    )
    relations = tuple(
        {
            "source": node_by_id[edge.source_id].label,
            "relation": edge.relation.value,
            "target": node_by_id[edge.target_id].label,
        }
        for edge in edges
    )
    return DemoAnalysis(
        entities,
        relations,
        tuple(node.to_dict() for node in nodes),
        tuple(edge.to_dict() for edge in edges),
    )


NODE_COLORS = {
    "Patient": "#fb7185",
    "Diagnosis": "#a78bfa",
    "Symptom": "#fbbf24",
    "Finding": "#2dd4bf",
    "Exam": "#60a5fa",
    "ExamResult": "#38bdf8",
    "Treatment": "#4ade80",
    "Medication": "#22c55e",
    "AnatomicalSite": "#f97316",
    "Measurement": "#94a3b8",
}


def graph_to_dot(analysis: DemoAnalysis) -> str:
    """Serialize the generated graph as safe Graphviz DOT."""
    lines = [
        "digraph clinical_graph {",
        'graph [bgcolor="transparent", rankdir="LR", pad="0.35", nodesep="0.55", ranksep="0.8"];',
        'node [shape="box", style="rounded,filled", fontname="Arial", fontsize="11", color="#334155", fontcolor="#0f172a"];',
        'edge [fontname="Arial", fontsize="9", color="#64748b", fontcolor="#475569", arrowsize="0.75"];',
    ]
    for node in analysis.nodes:
        node_id = json.dumps(node["node_id"])
        label = json.dumps(f'{node["label"]}\n{node["type"]}')
        color = NODE_COLORS.get(node["type"], "#cbd5e1")
        lines.append(f"{node_id} [label={label}, fillcolor={json.dumps(color)}];")
    for edge in analysis.edges:
        lines.append(
            f'{json.dumps(edge["source_id"])} -> {json.dumps(edge["target_id"])} '
            f'[label={json.dumps(edge["relation"])}];'
        )
    lines.append("}")
    return "\n".join(lines)


__all__ = ["DemoAnalysis", "analyze_text", "demo_vocabulary", "graph_to_dot"]
