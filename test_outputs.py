import json
import math
from pathlib import Path

APP = Path('/app')
RESULTS = APP / 'results'
PRED_PATH = RESULTS / 'predictions.normalized.jsonl'
REPORT_PATH = RESULTS / 'evaluation_report.json'
LABELS = ['billing', 'technical', 'account_access', 'shipping', 'cancellation']
ALLOWED_PREDICTIONS = set(LABELS + ['abstain'])
EXPECTED_REASONS = {
    'T-001': 'ok',
    'T-002': 'ok',
    'T-003': 'ok',
    'T-004': 'ok',
    'T-005': 'ok',
    'T-006': 'low_confidence',
    'T-007': 'ok',
    'T-008': 'unknown_label',
    'T-009': 'ok',
    'T-010': 'ok',
    'T-011': 'ok',
    'T-012': 'low_confidence',
    'T-013': 'ok',
    'T-014': 'low_confidence',
    'T-015': 'ok',
    'T-016': 'missing_prediction',
}
EXPECTED_LABELS = {
    'T-001': 'billing',
    'T-002': 'technical',
    'T-003': 'account_access',
    'T-004': 'shipping',
    'T-005': 'cancellation',
    'T-006': 'abstain',
    'T-007': 'technical',
    'T-008': 'abstain',
    'T-009': 'shipping',
    'T-010': 'billing',
    'T-011': 'billing',
    'T-012': 'abstain',
    'T-013': 'account_access',
    'T-014': 'abstain',
    'T-015': 'cancellation',
    'T-016': 'abstain',
}
EXPECTED_SOURCE = {
    'T-002': 'tech-support',
    'T-004': 'delivery/shipping',
    'T-010': 'billing',
    'T-014': 'shipment',
    'T-016': None,
}
EXPECTED_REPORT = {
    'total': 16,
    'coverage': 0.6875,
    'accuracy': 0.625,
    'macro_f1': 0.754286,
    'abstentions': 5,
    'ignored_extra_predictions': 1,
    'duplicate_ticket_ids': ['T-002', 'T-004', 'T-010'],
    'per_class': {
        'billing': {'support': 4, 'tp': 2, 'fp': 1, 'fn': 2, 'precision': 0.666667, 'recall': 0.5, 'f1': 0.571429},
        'technical': {'support': 3, 'tp': 2, 'fp': 0, 'fn': 1, 'precision': 1.0, 'recall': 0.666667, 'f1': 0.8},
        'account_access': {'support': 3, 'tp': 2, 'fp': 0, 'fn': 1, 'precision': 1.0, 'recall': 0.666667, 'f1': 0.8},
        'shipping': {'support': 3, 'tp': 2, 'fp': 0, 'fn': 1, 'precision': 1.0, 'recall': 0.666667, 'f1': 0.8},
        'cancellation': {'support': 3, 'tp': 2, 'fp': 0, 'fn': 1, 'precision': 1.0, 'recall': 0.666667, 'f1': 0.8},
    },
}


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def assert_close(actual, expected, tol=1e-6):
    assert isinstance(actual, (int, float)), f'Expected numeric value, got {actual!r}'
    assert math.isclose(float(actual), float(expected), rel_tol=0, abs_tol=tol), f'{actual!r} != {expected!r}'


def test_required_output_files_exist():
    """Both required result artifacts must exist at the exact /app/results paths from instruction.md."""
    assert PRED_PATH.is_file(), 'Missing /app/results/predictions.normalized.jsonl'
    assert REPORT_PATH.is_file(), 'Missing /app/results/evaluation_report.json'


def test_normalized_predictions_schema_and_order():
    """Normalized predictions must contain exactly one sorted row per gold ticket and no extra ticket IDs."""
    rows = read_jsonl(PRED_PATH)
    assert len(rows) == 16
    ids = [row.get('ticket_id') for row in rows]
    assert ids == sorted(EXPECTED_LABELS), 'Rows must be sorted by ticket_id and contain exactly the gold IDs'
    for row in rows:
        assert set(row) == {'ticket_id', 'predicted_label', 'confidence', 'source_label', 'reason'}
        assert row['predicted_label'] in ALLOWED_PREDICTIONS
        assert row['reason'] in {'ok', 'low_confidence', 'unknown_label', 'missing_prediction'}
        if row['reason'] == 'missing_prediction':
            assert row['confidence'] is None
            assert row['source_label'] is None
        else:
            assert isinstance(row['confidence'], (int, float))
            assert 0.0 <= float(row['confidence']) <= 1.0
            assert isinstance(row['source_label'], str)


def test_normalization_duplicate_threshold_and_abstention_rules():
    """Predicted labels, chosen source labels, and abstention reasons must reflect alias, duplicate, and confidence rules."""
    by_id = {row['ticket_id']: row for row in read_jsonl(PRED_PATH)}
    for tid, expected_label in EXPECTED_LABELS.items():
        assert by_id[tid]['predicted_label'] == expected_label, f'Wrong predicted_label for {tid}'
        assert by_id[tid]['reason'] == EXPECTED_REASONS[tid], f'Wrong reason for {tid}'
    for tid, expected_source in EXPECTED_SOURCE.items():
        assert by_id[tid]['source_label'] == expected_source, f'Wrong chosen source_label for {tid}'
    assert by_id['T-007']['confidence'] == 1.0, 'Missing confidence must default to 1.0'
    assert by_id['T-014']['confidence'] == 0.0, 'Invalid confidence must parse to 0.0'


def test_evaluation_report_top_level_metrics():
    """The evaluation report must include deterministic aggregate metrics and dataset accounting fields."""
    report = json.loads(REPORT_PATH.read_text(encoding='utf-8'))
    for key in ['total', 'coverage', 'accuracy', 'macro_f1', 'abstentions', 'ignored_extra_predictions', 'duplicate_ticket_ids', 'per_class']:
        assert key in report, f'Missing report field {key}'
    assert report['total'] == EXPECTED_REPORT['total']
    assert report['abstentions'] == EXPECTED_REPORT['abstentions']
    assert report['ignored_extra_predictions'] == EXPECTED_REPORT['ignored_extra_predictions']
    assert report['duplicate_ticket_ids'] == EXPECTED_REPORT['duplicate_ticket_ids']
    assert_close(report['coverage'], EXPECTED_REPORT['coverage'])
    assert_close(report['accuracy'], EXPECTED_REPORT['accuracy'])
    assert_close(report['macro_f1'], EXPECTED_REPORT['macro_f1'])


def test_per_class_metrics_are_correct_and_complete():
    """Per-class support, confusion counts, precision, recall, and F1 must match the policy for all labels."""
    report = json.loads(REPORT_PATH.read_text(encoding='utf-8'))
    assert list(report['per_class'].keys()) == LABELS
    for label in LABELS:
        actual = report['per_class'][label]
        expected = EXPECTED_REPORT['per_class'][label]
        assert actual['support'] == expected['support']
        assert actual['tp'] == expected['tp']
        assert actual['fp'] == expected['fp']
        assert actual['fn'] == expected['fn']
        assert_close(actual['precision'], expected['precision'])
        assert_close(actual['recall'], expected['recall'])
        assert_close(actual['f1'], expected['f1'])
