from project1.src.interactive_demo import analyze_text, graph_to_dot


def test_interactive_demo_returns_entities_relations_and_graph():
    analysis = analyze_text(
        "The fictional patient reported abdominal pain. A CT scan was performed "
        "and acute pancreatitis was diagnosed."
    )

    labels = {entity["entity"] for entity in analysis.entities}
    relations = {(item["source"], item["relation"], item["target"]) for item in analysis.relations}

    assert {"abdominal pain", "computed tomography", "acute pancreatitis"} <= labels
    assert ("patient", "PRESENTS_WITH", "abdominal pain") in relations
    assert ("patient", "UNDERWENT_EXAM", "computed tomography") in relations
    assert ("patient", "DIAGNOSED_WITH", "acute pancreatitis") in relations
    assert len(analysis.nodes) >= 4
    assert len(analysis.edges) >= 3

    dot = graph_to_dot(analysis)
    assert dot.startswith("digraph clinical_graph")
    assert "PRESENTS_WITH" in dot
