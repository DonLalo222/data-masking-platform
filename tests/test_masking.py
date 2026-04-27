from __future__ import annotations

import pytest

from app.masking.anonymize import anonymize
from app.masking.pseudonymize import pseudonymize
from app.masking.obfuscate import obfuscate
from app.masking.tokenize import tokenize
from app.masking.encrypt import encrypt
from app.masking.generalize import generalize
from app.masking.shuffle import shuffle
from app.masking.engine import apply_masking
from app.models.rule import ColumnRule, MaskingStrategy


# ---------------------------------------------------------------------------
# anonymize
# ---------------------------------------------------------------------------

def test_anonymize_returns_none():
    assert anonymize("hello") is None
    assert anonymize(42) is None
    assert anonymize(None) is None


# ---------------------------------------------------------------------------
# pseudonymize
# ---------------------------------------------------------------------------

def test_pseudonymize_is_deterministic():
    assert pseudonymize("John Smith") == pseudonymize("John Smith")


def test_pseudonymize_different_inputs_differ():
    assert pseudonymize("Alice") != pseudonymize("Bob")


def test_pseudonymize_email_detection():
    result = pseudonymize("user@example.com")
    assert "@" in result


# ---------------------------------------------------------------------------
# obfuscate
# ---------------------------------------------------------------------------

def test_obfuscate_default():
    result = obfuscate("4111123456789010")
    assert result.endswith("9010")
    assert "*" in result


def test_obfuscate_email():
    result = obfuscate("user@mail.com")
    assert "@" in result
    assert result.startswith("u")
    assert "***" in result


def test_obfuscate_short_value():
    result = obfuscate("abc")
    assert result == "***"


# ---------------------------------------------------------------------------
# tokenize
# ---------------------------------------------------------------------------

def test_tokenize_format():
    result = tokenize("hello")
    assert result.startswith("tok_")
    assert len(result) == 12  # "tok_" + 8 chars


def test_tokenize_deterministic():
    assert tokenize("hello") == tokenize("hello")


def test_tokenize_different_inputs_differ():
    assert tokenize("foo") != tokenize("bar")


# ---------------------------------------------------------------------------
# encrypt
# ---------------------------------------------------------------------------

def test_encrypt_returns_hex():
    result = encrypt("hello")
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_encrypt_deterministic():
    assert encrypt("data") == encrypt("data")


# ---------------------------------------------------------------------------
# generalize
# ---------------------------------------------------------------------------

def test_generalize_default_bucket():
    assert generalize(34) == "30-40"
    assert generalize(30) == "30-40"
    assert generalize(39) == "30-40"
    assert generalize(40) == "40-50"


def test_generalize_custom_bucket():
    assert generalize(34, bucket_size=5) == "30-35"
    assert generalize(100, bucket_size=25) == "100-125"


def test_generalize_non_numeric():
    assert generalize("hello") == "hello"


# ---------------------------------------------------------------------------
# shuffle
# ---------------------------------------------------------------------------

def test_shuffle_same_elements():
    values = [1, 2, 3, 4, 5]
    result = shuffle(values)
    assert sorted(result) == sorted(values)
    assert len(result) == len(values)


def test_shuffle_does_not_mutate_input():
    values = [1, 2, 3]
    original = list(values)
    shuffle(values)
    assert values == original


# ---------------------------------------------------------------------------
# masking engine
# ---------------------------------------------------------------------------

def test_engine_apply_masking():
    rows = [
        {"name": "Alice", "email": "alice@example.com", "age": 34, "id": 1},
        {"name": "Bob", "email": "bob@example.com", "age": 25, "id": 2},
    ]
    column_rules = [
        ColumnRule(column="name", strategy=MaskingStrategy.anonymize),
        ColumnRule(column="email", strategy=MaskingStrategy.obfuscate),
        ColumnRule(column="age", strategy=MaskingStrategy.generalize, options={"bucket_size": 10}),
        ColumnRule(column="id", strategy=MaskingStrategy.keep),
    ]
    result = apply_masking(rows, column_rules)

    assert result[0]["name"] is None
    assert result[1]["name"] is None
    assert "@" in result[0]["email"]
    assert result[0]["age"] == "30-40"
    assert result[1]["age"] == "20-30"
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2


def test_engine_shuffle_strategy():
    rows = [{"val": i} for i in range(10)]
    column_rules = [ColumnRule(column="val", strategy=MaskingStrategy.shuffle)]
    result = apply_masking(rows, column_rules)
    original_values = sorted([r["val"] for r in rows])
    result_values = sorted([r["val"] for r in result])
    assert original_values == result_values


def test_engine_empty_rows():
    assert apply_masking([], []) == []


def test_engine_columns_without_rule_are_kept():
    rows = [{"a": 1, "b": 2}]
    column_rules = [ColumnRule(column="a", strategy=MaskingStrategy.anonymize)]
    result = apply_masking(rows, column_rules)
    assert result[0]["b"] == 2
    assert result[0]["a"] is None
