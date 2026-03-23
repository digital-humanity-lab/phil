"""Lexical feature quantifier."""
from __future__ import annotations
import re
from collections import Counter
import numpy as np

ARGUMENT_MARKERS = {"therefore", "because", "however", "thus", "hence",
                     "although", "nevertheless", "moreover", "consequently",
                     "furthermore", "nonetheless", "accordingly"}

class LexicalQuantifier:
    def feature_names(self) -> list[str]:
        return ["n_tokens", "n_types", "ttr", "hapax_ratio",
                "mean_word_length", "argument_marker_density",
                "sentence_count", "technical_ratio"]

    def quantify(self, texts: list[str]) -> np.ndarray:
        n = len(texts)
        features = np.zeros((n, len(self.feature_names())))
        for i, text in enumerate(texts):
            tokens = re.findall(r'\b\w+\b', text.lower())
            n_tok = len(tokens)
            counter = Counter(tokens)
            n_typ = len(counter)
            hapax = sum(1 for c in counter.values() if c == 1)
            sentences = re.split(r'[.!?]+', text)
            markers = sum(1 for t in tokens if t in ARGUMENT_MARKERS)
            long_words = sum(1 for t in tokens if len(t) > 10)

            features[i] = [
                n_tok, n_typ,
                n_typ / n_tok if n_tok > 0 else 0,
                hapax / n_typ if n_typ > 0 else 0,
                np.mean([len(t) for t in tokens]) if tokens else 0,
                markers / n_tok if n_tok > 0 else 0,
                len([s for s in sentences if s.strip()]),
                long_words / n_tok if n_tok > 0 else 0,
            ]
        return features
