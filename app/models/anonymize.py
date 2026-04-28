from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class OperatorConfig(BaseModel):
    """Configuration for a single anonymization operator."""

    type: Literal["replace", "redact", "hash", "encrypt", "mask", "keep"] = Field(
        "replace",
        description=(
            "Anonymization strategy to apply:\n"
            "- **replace** – substitute with a fixed string (default: `<ENTITY_TYPE>`)\n"
            "- **redact** – remove the entity entirely\n"
            "- **hash** – replace with a hash digest\n"
            "- **encrypt** – AES-CBC encryption (requires a 16-byte base64 key)\n"
            "- **mask** – overwrite characters with a masking character\n"
            "- **keep** – preserve the original value"
        ),
    )
    params: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Operator-specific parameters:\n"
            "- `replace`: `{\"new_value\": \"REDACTED\"}`\n"
            "- `hash`: `{\"hash_type\": \"sha256\"}` — options: md5, sha256, sha512\n"
            "- `encrypt`: `{\"key\": \"<16-byte-base64-key>\"}`\n"
            "- `mask`: `{\"masking_char\": \"*\", \"chars_to_mask\": 5, \"from_end\": false}`\n"
            "- `redact` / `keep`: no parameters"
        ),
    )


class AnonymizeRequest(BaseModel):
    text: str = Field(..., description="Text whose PII should be anonymized.")
    language: str = Field("en", description="BCP-47 language code.")
    entities: Optional[List[str]] = Field(
        None,
        description="Limit anonymization to these entity types. Omit to process all detected entities.",
    )
    score_threshold: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score for an entity to be anonymized.",
    )
    operators: Optional[Dict[str, OperatorConfig]] = Field(
        None,
        description=(
            "Per-entity operator overrides. "
            "Keys are entity type strings (e.g. `PERSON`) or `DEFAULT` for a fallback. "
            "Omitting this field applies the `replace` operator to all entities."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Hello John Smith, your SSN is 078-05-1120 and e-mail is john@example.com",
                "language": "en",
                "operators": {
                    "PERSON": {"type": "replace", "params": {"new_value": "[NAME]"}},
                    "EMAIL_ADDRESS": {
                        "type": "mask",
                        "params": {"masking_char": "*", "chars_to_mask": 10, "from_end": False},
                    },
                    "US_SSN": {"type": "hash", "params": {"hash_type": "sha256"}},
                    "DEFAULT": {"type": "replace"},
                },
            }
        }
    }


class AnonymizedItem(BaseModel):
    operator: str = Field(..., description="Operator that was applied.")
    entity_type: str = Field(..., description="Entity type that was anonymized.")
    start: int = Field(..., description="Start index of the replacement in the output text.")
    end: int = Field(..., description="End index (exclusive) of the replacement in the output text.")
    text: str = Field(..., description="Replacement text that was inserted.")


class AnonymizeResponse(BaseModel):
    text: str = Field(..., description="Fully anonymized output text.")
    items: List[AnonymizedItem] = Field(..., description="Details of each anonymization applied.")


class BatchAnonymizeRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to anonymize.")
    language: str = Field("en", description="BCP-47 language code.")
    entities: Optional[List[str]] = Field(None, description="Limit to these entity types.")
    score_threshold: float = Field(0.5, ge=0.0, le=1.0)
    operators: Optional[Dict[str, OperatorConfig]] = Field(
        None, description="Per-entity operator overrides (applied to every text)."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "texts": [
                    "My name is Alice and I live in London.",
                    "Contact Bob at bob@example.com or 555-867-5309.",
                ],
                "language": "en",
                "operators": {"DEFAULT": {"type": "replace"}},
            }
        }
    }


class BatchAnonymizeResponse(BaseModel):
    results: List[AnonymizeResponse]
