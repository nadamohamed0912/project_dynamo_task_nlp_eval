You are working in `/app` on an offline NLP ticket-triage evaluation. The visible inputs are:

- `/app/data/tickets.gold.jsonl`
- `/app/data/model_outputs.raw.jsonl`
- `/app/config/label_aliases.json`
- `/app/specs/evaluation_policy.md`
- `/app/tools/evaluate_tickets.py` (known incomplete; repair it or ignore it)

Create these output files:

1. `/app/results/predictions.normalized.jsonl`
2. `/app/results/evaluation_report.json`

Follow `/app/specs/evaluation_policy.md` exactly. The normalized predictions file must contain one JSON object per gold ticket, sorted by `ticket_id`, with this schema:

```json
{"ticket_id":"T-001","predicted_label":"billing","confidence":0.91,"source_label":"Billing Question","reason":"ok"}
```

`predicted_label` must be one of `billing`, `technical`, `account_access`, `shipping`, `cancellation`, or `abstain`. For `missing_prediction`, use `null` for `confidence` and `source_label`. For other rows, preserve the chosen raw `model_label` as `source_label` and write the parsed confidence as a number.

The evaluation report must be JSON with this top-level schema:

```json
{
  "total": 16,
  "coverage": 0.0,
  "accuracy": 0.0,
  "macro_f1": 0.0,
  "abstentions": 0,
  "ignored_extra_predictions": 0,
  "duplicate_ticket_ids": ["T-002"],
  "per_class": {
    "billing": {"support": 0, "tp": 0, "fp": 0, "fn": 0, "precision": 0.0, "recall": 0.0, "f1": 0.0}
  }
}
```

Include all five canonical labels under `per_class` in this order: `billing`, `technical`, `account_access`, `shipping`, `cancellation`. Round metric floats to six decimal places. Do not include raw predictions for IDs absent from the gold file in the normalized predictions.

You have 3600 seconds to complete this task.
