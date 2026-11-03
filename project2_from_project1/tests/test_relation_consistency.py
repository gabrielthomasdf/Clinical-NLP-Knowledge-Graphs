from project2_from_project1.src.clinical_documents import CanonicalRelation
from project2_from_project1.src.relation_consistency import count_negation_conflicts, enforce_negation_consistency
from project2_from_project1.src.relation_evaluation import RelationPrediction


def _prediction(document, source, target, label):
    return RelationPrediction(document, source, target, label, label, "test-rules", {}, model_version="v1")


def test_only_the_negated_mention_is_suppressed():
    predictions = (
        _prediction("doc", "patient", "fever:1", "HAS_FINDING"),
        _prediction("doc", "no:1", "fever:1", "NEGATES"),
        _prediction("doc", "patient", "fever:2", "HAS_FINDING"),
        _prediction("other", "patient", "fever:1", "HAS_FINDING"),
    )
    corrected = enforce_negation_consistency(predictions)
    assert count_negation_conflicts(predictions) == 1
    assert count_negation_conflicts(corrected) == 0
    assert len(corrected) == len(predictions)
    assert corrected[0].canonical_label is CanonicalRelation.NO_RELATION
    assert corrected[0].evidence["consistency"]["original_label"] == "HAS_FINDING"
    assert corrected[1:] == predictions[1:]
    assert enforce_negation_consistency(corrected) == corrected


def test_rejects_duplicate_pairs():
    prediction = _prediction("doc", "patient", "fever:1", "HAS_FINDING")
    try:
        enforce_negation_consistency((prediction, prediction))
    except ValueError as error:
        assert "duplicate" in str(error)
    else:
        raise AssertionError("duplicate relation pair accepted")
