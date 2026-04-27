from __future__ import annotations

from typing import Any, Dict, List

from app.masking.anonymize import anonymize
from app.masking.pseudonymize import pseudonymize
from app.masking.obfuscate import obfuscate
from app.masking.tokenize import tokenize
from app.masking.encrypt import encrypt
from app.masking.generalize import generalize
from app.masking.shuffle import shuffle
from app.models.rule import ColumnRule, MaskingStrategy


def apply_masking(rows: List[Dict[str, Any]], column_rules: List[ColumnRule]) -> List[Dict[str, Any]]:
    """Apply masking rules to a list of row dicts and return the masked rows."""

    if not rows:
        return rows

    rule_map: Dict[str, ColumnRule] = {r.column: r for r in column_rules}

    shuffle_columns: Dict[str, List[Any]] = {}
    for rule in column_rules:
        if rule.strategy == MaskingStrategy.shuffle:
            shuffle_columns[rule.column] = shuffle([row.get(rule.column) for row in rows])

    masked_rows: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows):
        masked_row: Dict[str, Any] = {}
        for col, val in row.items():
            rule = rule_map.get(col)
            if rule is None:
                masked_row[col] = val
                continue

            strategy = rule.strategy
            options = rule.options or {}

            if strategy == MaskingStrategy.keep:
                masked_row[col] = val
            elif strategy == MaskingStrategy.anonymize:
                masked_row[col] = anonymize(val)
            elif strategy == MaskingStrategy.pseudonymize:
                masked_row[col] = pseudonymize(val)
            elif strategy == MaskingStrategy.obfuscate:
                masked_row[col] = obfuscate(val)
            elif strategy == MaskingStrategy.tokenize:
                masked_row[col] = tokenize(val)
            elif strategy == MaskingStrategy.encrypt:
                masked_row[col] = encrypt(val)
            elif strategy == MaskingStrategy.generalize:
                bucket_size = int(options.get("bucket_size", 10))
                masked_row[col] = generalize(val, bucket_size)
            elif strategy == MaskingStrategy.shuffle:
                masked_row[col] = shuffle_columns[col][idx]
            else:
                masked_row[col] = val

        masked_rows.append(masked_row)

    return masked_rows
