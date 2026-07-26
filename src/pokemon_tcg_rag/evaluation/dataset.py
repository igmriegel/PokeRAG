"""
Evaluation dataset loader.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pokemon_tcg_rag.domain.models import DocumentSource

LOGGER = logging.getLogger(__name__)

EXPECTED_CASE_COUNT = 100
DEFAULT_DATASET_PATH = Path("data/evaluation/benchmark_100_questions.json")


class EvalTestCase(BaseModel):
    """Single benchmark question used by the evaluation harness."""

    model_config = ConfigDict(frozen=True)

    question_id: str
    question: str
    ground_truth_doc_ids: list[str] = Field(min_length=1)
    expected_source: DocumentSource
    reference_answer: str

    @field_validator("question_id", "question", "reference_answer")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("field must not be blank")
        return value.strip()

    @field_validator("ground_truth_doc_ids")
    @classmethod
    def _doc_ids_must_be_valid(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("ground_truth_doc_ids must not be empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("ground_truth_doc_ids must be unique")
        return cleaned

    @property
    def expected_doc_ids(self) -> list[str]:
        """Backward-compatible alias for legacy callers."""
        return self.ground_truth_doc_ids


class EvaluationDatasetLoader:
    """Load the 100-question benchmark from disk."""

    def __init__(self, dataset_path: str | Path = DEFAULT_DATASET_PATH) -> None:
        self.dataset_path = Path(dataset_path)

    def load_dataset(self) -> list[EvalTestCase]:
        """Load and validate the benchmark file."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {self.dataset_path}")

        payload = json.loads(self.dataset_path.read_text(encoding="utf-8"))
        raw_cases = payload.get("cases") if isinstance(payload, dict) else payload

        if not isinstance(raw_cases, list):
            raise ValueError("Benchmark dataset must be a list of cases")

        cases: list[EvalTestCase] = []
        seen_ids: set[str] = set()
        for index, item in enumerate(raw_cases, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"Case {index} must be an object")
            normalized = self._normalize_case(item, index)
            case = EvalTestCase.model_validate(normalized)
            if case.question_id in seen_ids:
                raise ValueError(f"Duplicate question_id detected: {case.question_id}")
            seen_ids.add(case.question_id)
            cases.append(case)

        if len(cases) != EXPECTED_CASE_COUNT:
            raise ValueError(
                f"Benchmark dataset must contain exactly {EXPECTED_CASE_COUNT} cases; found {len(cases)}"
            )

        LOGGER.info(
            "benchmark_dataset_loaded path=%s cases=%s",
            self.dataset_path,
            len(cases),
        )
        return cases

    def _normalize_case(self, item: dict[str, Any], index: int) -> dict[str, Any]:
        """Adapt legacy payloads and validate required fields."""
        question_id = item.get("question_id") or f"Q{index:03d}"
        question = item.get("question")
        expected_source = item.get("expected_source")
        ground_truth_doc_ids = item.get("ground_truth_doc_ids") or item.get("expected_doc_ids")
        reference_answer = item.get("reference_answer")

        if reference_answer is None:
            keywords = item.get("expected_answer_keywords")
            if isinstance(keywords, list) and keywords:
                reference_answer = "; ".join(
                    str(keyword).strip() for keyword in keywords if str(keyword).strip()
                )

        normalized = {
            "question_id": question_id,
            "question": question,
            "ground_truth_doc_ids": ground_truth_doc_ids,
            "expected_source": expected_source,
            "reference_answer": reference_answer,
        }

        missing = [field for field, value in normalized.items() if value is None]
        if missing:
            raise ValueError(f"Case {index} is missing required fields: {', '.join(missing)}")
        return normalized
