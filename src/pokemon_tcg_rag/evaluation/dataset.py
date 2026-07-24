"""
Evaluation Dataset Loader.
"""

import json
import logging
from pathlib import Path
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EvalTestCase(BaseModel):
    """Single evaluation query test case."""
    question_id: str
    question: str
    expected_doc_ids: list[str]
    expected_answer_keywords: list[str]


class EvaluationDatasetLoader:
    """Loads benchmark dataset of 100 questions for RAG evaluation."""

    def __init__(self, dataset_path: str = "data/evaluation/benchmark_100_questions.json") -> None:
        self.dataset_path = Path(dataset_path)

    def load_dataset(self) -> list[EvalTestCase]:
        """Load evaluation questions dataset."""
        if not self.dataset_path.exists():
            logger.warning("Dataset file not found at %s. Returning mock dataset.", self.dataset_path)
            return [
                EvalTestCase(
                    question_id="Q001",
                    question="Can Rare Candy be played on the first turn of the game?",
                    expected_doc_ids=["rulebook_pdf_p15", "pokegym_102"],
                    expected_answer_keywords=["first turn", "Rare Candy", "evolution"]
                )
            ]

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [EvalTestCase(**item) for item in data]
