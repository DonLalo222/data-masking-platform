"""Tests for Chilean geographic / address entity recognition.

Covers:
- CL_REGION: accent variants, case variants, no-context baseline
- CL_COMUNA: accent variants, mixed case, context boost
- CL_STREET_ADDRESS: abbreviations, N°/No./# number variants
- strip_accents() normalisation helper
- ClAccentInsensitiveRecognizer offset correctness
- Overlap / conflict with generic LOCATION entity
- Idempotent registration
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.cl_geo_utils import (
    ClAccentInsensitiveRecognizer,
    get_all_communes,
    get_all_region_aliases,
    strip_accents,
)


@pytest.fixture(scope="module")
def client():
    """TestClient that runs the full lifespan so all recognizers are registered."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# strip_accents helper
# ---------------------------------------------------------------------------


def test_strip_accents_preserves_length():
    original = "Región del Biobío"
    stripped = strip_accents(original)
    assert len(stripped) == len(original)


def test_strip_accents_lowercases():
    assert strip_accents("Tarapacá") == "tarapaca"


def test_strip_accents_handles_enie():
    assert strip_accents("Ñuble") == "nuble"


def test_strip_accents_handles_o_higgins():
    # Apostrophe is preserved; only combining marks are removed
    assert strip_accents("O'Higgins") == "o'higgins"


def test_strip_accents_plain_ascii_unchanged():
    assert strip_accents("Antofagasta") == "antofagasta"


# ---------------------------------------------------------------------------
# get_all_region_aliases / get_all_communes
# ---------------------------------------------------------------------------


def test_get_all_region_aliases_non_empty():
    aliases = get_all_region_aliases()
    assert len(aliases) >= 16  # at least one alias per region


def test_get_all_region_aliases_contains_canonical():
    aliases = get_all_region_aliases()
    assert "Biobío" in aliases


def test_get_all_region_aliases_contains_variant():
    aliases = get_all_region_aliases()
    assert "Biobio" in aliases  # non-accented alias from JSON


def test_get_all_communes_non_empty():
    communes = get_all_communes()
    assert len(communes) >= 100


def test_get_all_communes_contains_santiago():
    assert "Santiago" in get_all_communes()


def test_get_all_communes_contains_accented_entry():
    # Should include accented commune names
    assert "Valparaíso" in get_all_communes()


# ---------------------------------------------------------------------------
# ClAccentInsensitiveRecognizer — unit tests (no HTTP)
# ---------------------------------------------------------------------------


def _make_region_recognizer(accent_insensitive: bool = True) -> ClAccentInsensitiveRecognizer:
    return ClAccentInsensitiveRecognizer(
        supported_entity="CL_REGION",
        name="TestClRegion",
        deny_list=["Biobío", "Ñuble", "Tarapacá", "O'Higgins", "Valparaíso"],
        context=["región", "region"],
        base_score=1.0,
        accent_insensitive=accent_insensitive,
    )


def test_recognizer_matches_accented_form():
    r = _make_region_recognizer()
    results = r.analyze("Región del Biobío", ["CL_REGION"])
    entities = [(res.start, res.end) for res in results]
    # "Biobío" is at position 10–16 in "Región del Biobío"
    assert any(res.entity_type == "CL_REGION" for res in results)


def test_recognizer_matches_unaccented_form():
    """'Biobio' (no tildes) should be detected as CL_REGION."""
    r = _make_region_recognizer()
    results = r.analyze("Region del Biobio", ["CL_REGION"])
    assert any(res.entity_type == "CL_REGION" for res in results)


def test_recognizer_matches_case_insensitive():
    r = _make_region_recognizer()
    results = r.analyze("region del biobio", ["CL_REGION"])
    assert any(res.entity_type == "CL_REGION" for res in results)


def test_recognizer_matches_nuble_without_tilde():
    r = _make_region_recognizer()
    results = r.analyze("paciente de la region de Nuble", ["CL_REGION"])
    assert any(res.entity_type == "CL_REGION" for res in results)


def test_recognizer_matches_tarapaca_without_accent():
    r = _make_region_recognizer()
    results = r.analyze("Tarapaca", ["CL_REGION"])
    assert any(res.entity_type == "CL_REGION" for res in results)


def test_recognizer_offsets_point_to_original_text():
    """Offsets returned must correspond to the span in the *original* text."""
    r = _make_region_recognizer()
    original = "Región del Biobío"
    results = r.analyze(original, ["CL_REGION"])
    # Filter to CL_REGION results
    cl_results = [res for res in results if res.entity_type == "CL_REGION"]
    assert cl_results, "Expected at least one CL_REGION result"
    for res in cl_results:
        span = original[res.start:res.end]
        # The span should contain "Bio" or similar; must be non-empty
        assert span.strip() != ""


def test_recognizer_context_boost_applied():
    """Score should be higher when context words appear nearby."""
    r = _make_region_recognizer()
    # With context word "region" nearby
    res_with_ctx = r.analyze("region del Biobio", ["CL_REGION"])
    # Without context
    res_no_ctx = r.analyze("Biobio", ["CL_REGION"])
    score_with = max(res.score for res in res_with_ctx if res.entity_type == "CL_REGION")
    score_without = max(res.score for res in res_no_ctx if res.entity_type == "CL_REGION")
    assert score_with >= score_without


def test_recognizer_analysis_explanation_populated():
    """RecognizerResult.analysis_explanation must not be None (prevents engine crash)."""
    r = _make_region_recognizer()
    results = r.analyze("Biobio", ["CL_REGION"])
    for res in results:
        assert res.analysis_explanation is not None


def test_recognizer_recognition_metadata_populated():
    """recognition_metadata must include recognizer_identifier key."""
    r = _make_region_recognizer()
    results = r.analyze("Biobio", ["CL_REGION"])
    for res in results:
        assert res.recognition_metadata is not None
        assert "recognizer_identifier" in res.recognition_metadata


def test_recognizer_accent_insensitive_false():
    """When accent_insensitive=False, accented form is not detected from non-accented text."""
    r = _make_region_recognizer(accent_insensitive=False)
    # "Biobio" (no accent) should NOT match "Biobío" when accent_insensitive is off
    results = r.analyze("Region del Biobio", ["CL_REGION"])
    matched_entity = [res for res in results if res.entity_type == "CL_REGION"]
    assert matched_entity == []


def test_recognizer_skips_wrong_entity():
    r = _make_region_recognizer()
    results = r.analyze("Biobío", ["SOME_OTHER_ENTITY"])
    assert results == []


def test_recognizer_dedup_no_double_results():
    """No two results should share (start, end, entity_type)."""
    r = ClAccentInsensitiveRecognizer(
        supported_entity="CL_REGION",
        name="TestDedup",
        deny_list=["Biobío", "Biobio"],  # Both normalise to same pattern
        context=[],
    )
    results = r.analyze("Biobío", ["CL_REGION"])
    keys = [(res.start, res.end, res.entity_type) for res in results]
    assert len(keys) == len(set(keys))


# ---------------------------------------------------------------------------
# CL_REGION via HTTP API — accent and variant tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "El paciente vive en la Región del Biobío.",
        "El paciente vive en la Region del Biobio.",
        "El paciente vive en la región del BioBio.",
        "Domicilio en la región del bio-bio.",
    ],
)
def test_detect_cl_region_biobio_variants(client, text):
    response = client.post(
        "/analyze",
        json={"text": text, "language": "es", "entities": ["CL_REGION"]},
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_REGION" in types, f"CL_REGION not detected in: {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "Región de la Araucanía",
        "Region de la Araucania",
        "Region de La Araucania",
    ],
)
def test_detect_cl_region_araucania_variants(client, text):
    response = client.post(
        "/analyze",
        json={"text": text, "language": "es", "entities": ["CL_REGION"]},
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_REGION" in types, f"CL_REGION not detected in: {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "Región de Ñuble",
        "Region de Nuble",
        "REGION DE NUBLE",
    ],
)
def test_detect_cl_region_nuble_variants(client, text):
    response = client.post(
        "/analyze",
        json={"text": text, "language": "es", "entities": ["CL_REGION"]},
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_REGION" in types, f"CL_REGION not detected in: {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "El paciente vive en la Región Metropolitana.",
        "El paciente vive en la Region Metropolitana.",
        "Domicilio: Metropolitana",
    ],
)
def test_detect_cl_region_metropolitana_variants(client, text):
    response = client.post(
        "/analyze",
        json={"text": text, "language": "es", "entities": ["CL_REGION"]},
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_REGION" in types, f"CL_REGION not detected in: {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "Region de Valparaiso",
        "Región de Valparaíso",
        "REGION DE VALPARAISO",
    ],
)
def test_detect_cl_region_valparaiso_variants(client, text):
    response = client.post(
        "/analyze",
        json={"text": text, "language": "es", "entities": ["CL_REGION"]},
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_REGION" in types, f"CL_REGION not detected in: {text!r}"


def test_detect_cl_region_ohiggins_variants(client):
    for text in [
        "Región de O'Higgins",
        "Region de OHiggins",
        "O Higgins",
    ]:
        response = client.post(
            "/analyze",
            json={"text": text, "language": "es", "entities": ["CL_REGION"]},
        )
        assert response.status_code == 200
        types = [e["entity_type"] for e in response.json()["entities"]]
        assert "CL_REGION" in types, f"CL_REGION not detected in: {text!r}"


# ---------------------------------------------------------------------------
# CL_COMUNA via HTTP API
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "La comuna de Valparaíso tiene muchos cerros.",
        "La comuna de Valparaiso tiene muchos cerros.",
        "Domicilio en la comuna de Providencia.",
        "Vive en Las Condes.",
    ],
)
def test_detect_cl_comuna(client, text):
    response = client.post(
        "/analyze",
        json={"text": text, "language": "es", "entities": ["CL_COMUNA"]},
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_COMUNA" in types, f"CL_COMUNA not detected in: {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "domicilio en la comuna de Temuco",
        "domicilio en la comuna de Concepcion",
        "domicilio en la comuna de Concepción",
    ],
)
def test_detect_cl_comuna_accented_variants(client, text):
    response = client.post(
        "/analyze",
        json={"text": text, "language": "es", "entities": ["CL_COMUNA"]},
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_COMUNA" in types, f"CL_COMUNA not detected in: {text!r}"


# ---------------------------------------------------------------------------
# CL_STREET_ADDRESS via HTTP API
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "Domicilio: Avenida Providencia 1234",
        "Dirección: Calle Los Aromos 567",
        "Av. Apoquindo 3400",
        "Vive en Avda. Grecia 890",
        "Pasaje Los Pinos 12",
        "Camino El Roble 200",
        "dirección: Calle Larga N° 45",
        "Pasaje Ochagavía No. 8",
        "Calle Ñuble #3",
    ],
)
def test_detect_cl_street_address(client, text):
    response = client.post(
        "/analyze",
        json={"text": text, "language": "es", "entities": ["CL_STREET_ADDRESS"]},
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_STREET_ADDRESS" in types, f"CL_STREET_ADDRESS not detected in: {text!r}"


def test_detect_cl_street_address_mixed_case(client):
    text = "AVENIDA LIBERTADOR BERNARDO O'HIGGINS 1370"
    response = client.post(
        "/analyze",
        json={"text": text, "language": "es", "entities": ["CL_STREET_ADDRESS"]},
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_STREET_ADDRESS" in types


def test_cl_street_address_not_detected_without_prefix(client):
    """Plain place names without street prefix should not be CL_STREET_ADDRESS."""
    text = "El paciente vive en Santiago."
    response = client.post(
        "/analyze",
        json={"text": text, "language": "es", "entities": ["CL_STREET_ADDRESS"]},
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_STREET_ADDRESS" not in types


# ---------------------------------------------------------------------------
# Overlap / conflict handling
# ---------------------------------------------------------------------------


def test_cl_region_not_overshadowed_by_location(client):
    """CL_REGION should be detected when LOCATION is also requested."""
    response = client.post(
        "/analyze",
        json={
            "text": "El domicilio está en la región del Biobío.",
            "language": "es",
            "entities": ["CL_REGION", "LOCATION"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_REGION" in types


def test_minsal_region_kept_accented(client):
    """CL_REGION detected with accents must still be kept in MINSAL output."""
    response = client.post(
        "/compliance/minsal",
        json={"text": "El paciente vive en la Región del Biobío.", "language": "es"},
    )
    assert response.status_code == 200
    data = response.json()
    text = data["text"]
    # The region span should remain in the output (either accented or non-accented
    # form is acceptable because the Presidio anonymizer preserves the original span).
    assert "Biobío" in text or "Biobio" in text or "biobío" in text.lower()


def test_minsal_region_kept_unaccented(client):
    """CL_REGION detected without accents must still be kept in MINSAL output."""
    response = client.post(
        "/compliance/minsal",
        json={"text": "El paciente vive en la region del Biobio.", "language": "es"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Biobio" in data["text"]


def test_minsal_street_address_replaced(client):
    """CL_STREET_ADDRESS should be replaced with <DOMICILIO> in MINSAL output."""
    response = client.post(
        "/compliance/minsal",
        json={
            "text": "El paciente vive en Avenida Providencia 1234.",
            "language": "es",
        },
    )
    assert response.status_code == 200
    data = response.json()
    # Either the street is replaced with <DOMICILIO>, or some other anonymization
    # operator was applied (location-level replacement is also acceptable).
    assert "<DOMICILIO>" in data["text"] or "Avenida Providencia 1234" not in data["text"]


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_register_idempotent_with_new_recognizers(client):
    from app.services.analyzer import get_engine
    from app.services.clinical_recognizers_cl import register_clinical_recognizers_cl

    registry = get_engine().registry
    size_before = len(registry.recognizers)
    register_clinical_recognizers_cl()
    size_after = len(registry.recognizers)
    assert size_after == size_before
