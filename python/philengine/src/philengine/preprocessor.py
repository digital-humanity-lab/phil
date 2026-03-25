"""Text preprocessor for classical and historical languages."""
from __future__ import annotations
import re, unicodedata

class PhilPreprocessor:
    def __init__(self, **normalizers):
        self._normalizers = normalizers

    def preprocess(self, text: str, language: str = "auto") -> str:
        if language == "auto":
            language = self._detect_script(text)
        normalizer = self._normalizers.get(language, "default")
        if normalizer == "cltk_normalize":
            return self._normalize_greek(text)
        elif normalizer == "kanbun_segment":
            return self._segment_kanbun(text)
        elif normalizer == "indic_transliterate":
            return self._transliterate_indic(text)
        return self._normalize_default(text)

    def _detect_script(self, text: str) -> str:
        for ch in text[:100]:
            if '\u4e00' <= ch <= '\u9fff': return "classical_chinese"
            if '\u0900' <= ch <= '\u097f': return "sanskrit"
            if '\u0370' <= ch <= '\u03ff': return "classical_greek"
        return "default"

    def _normalize_default(self, text: str) -> str:
        return unicodedata.normalize("NFC", text.strip())

    def _normalize_greek(self, text: str) -> str:
        text = unicodedata.normalize("NFD", text)
        text = re.sub(r'[\u0300-\u036f]', '', text)  # strip diacritics
        return unicodedata.normalize("NFC", text.lower())

    def _segment_kanbun(self, text: str) -> str:
        return re.sub(r'([。！？])', r'\1\n', text)

    def _transliterate_indic(self, text: str) -> str:
        return unicodedata.normalize("NFC", text)
