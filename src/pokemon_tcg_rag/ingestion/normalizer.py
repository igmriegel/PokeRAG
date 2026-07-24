"""
Document text normalization utilities.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

from pokemon_tcg_rag.domain.models import Document


class DocumentNormalizer:
    """Normalize extracted document text while preserving metadata."""

    _CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
    _DEHYPHENATE_RE = re.compile(r"(\w)-\s*\n\s*(\w)")
    _WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")
    _MULTI_NEWLINE_RE = re.compile(r"\n{2,}")

    def normalize(self, document: Document) -> Document:
        """Return a cleaned copy of ``document`` with a stable checksum."""
        text = unicodedata.normalize("NFKC", document.content)
        text = self._CONTROL_CHAR_RE.sub("", text)
        text = self._DEHYPHENATE_RE.sub(r"\1\2", text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = self._WHITESPACE_RE.sub(" ", text)
        text = self._MULTI_NEWLINE_RE.sub("\n", text)
        text = "\n".join(line.strip() for line in text.splitlines())
        text = re.sub(r"\n{2,}", "\n", text).strip()
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()

        return document.model_copy(
            update={
                "content": text,
                "metadata": document.metadata.model_copy(update={"checksum": checksum}),
            }
        )
