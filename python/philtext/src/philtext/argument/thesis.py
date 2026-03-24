"""Thesis extraction from philosophical texts.

Extracts philosophical claims/theses that are suitable for school
classification, concept alignment, and comparative analysis.

Unlike ArgumentExtractor (which finds premise-conclusion structures),
ThesisExtractor identifies standalone philosophical propositions:
ontological, epistemological, ethical, or metaphysical claims.

Design principle: A thesis is a sentence that, if you read it to a
philosopher, they would say "that's a philosophical claim I can
agree or disagree with" — not a contextual remark, example, or
bibliographic reference.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class ThesisType(str, Enum):
    ONTOLOGICAL = "ontological"          # About what exists / nature of being
    EPISTEMOLOGICAL = "epistemological"   # About knowledge / justification
    ETHICAL = "ethical"                   # About right/wrong, virtue, duty
    METAPHYSICAL = "metaphysical"        # About ultimate reality, causation
    AESTHETIC = "aesthetic"              # About beauty, art, taste
    LOGICAL = "logical"                  # About reasoning, truth, validity
    POLITICAL = "political"              # About justice, governance, rights
    EXISTENTIAL = "existential"          # About existence, freedom, meaning


@dataclass
class Thesis:
    """A philosophical thesis extracted from text."""
    text: str
    thesis_type: ThesisType | None = None
    confidence: float = 0.0
    source_paragraph: str = ""
    language: str = "en"
    is_negation: bool = False   # "X is NOT the case"
    universality: float = 0.0   # 0=particular, 1=universal claim
    metadata: dict = field(default_factory=dict)


# ── Philosophical vocabulary for thesis detection ────────────

# Words indicating abstract/universal philosophical claims
_PHILOSOPHICAL_TERMS = {
    "en": re.compile(
        r'\b('
        r'being|existence|essence|substance|reality|truth|knowledge|'
        r'consciousness|experience|perception|reason|understanding|'
        r'freedom|will|duty|virtue|justice|good|evil|beauty|'
        r'nature|soul|mind|self|spirit|absolute|infinite|'
        r'necessary|possible|impossible|universal|particular|'
        r'cause|effect|purpose|meaning|value|'
        r'moral|ethical|rational|empirical|transcendental|'
        r'a priori|a posteriori|synthetic|analytic'
        r')\b', re.IGNORECASE
    ),
    "ja": re.compile(
        r'('
        r'存在|本質|実在|真理|知識|認識|意識|経験|理性|悟性|'
        r'自由|意志|義務|徳|正義|善|悪|美|'
        r'自然|精神|魂|自己|絶対|無限|'
        r'必然|可能|不可能|普遍|特殊|'
        r'原因|目的|意味|価値|'
        r'道徳|倫理|理性|先験的|超越論的|'
        r'純粋経験|間柄|場所|絶対無|空|無|仁|道|理|気|'
        r'主客|分離|統一|直接|根本|根源|'
        r'自覚|行為|直観|弁証法|哲学|'
        r'人間|倫理学|個人|関係|他者|'
        r'ニヒリズム|虚無|超越|宗教'
        r')'
    ),
    "zh": re.compile(
        r'('
        r'仁|義|禮|智|信|道|德|理|気|性|命|天|'
        r'善|悪|真|美|知|行|心|物|無|有|空|'
        r'天下|万物|聖人|君子|小人'
        r')'
    ),
    "de": re.compile(
        r'\b('
        r'Sein|Dasein|Wesen|Substanz|Wahrheit|Erkenntnis|'
        r'Bewusstsein|Erfahrung|Vernunft|Verstand|'
        r'Freiheit|Wille|Pflicht|Tugend|Gerechtigkeit|'
        r'Geist|Seele|Selbst|Absolut|'
        r'Ding an sich|Erscheinung|Vorstellung|'
        r'transzendental|kategorisch|dialektisch'
        r')\b', re.IGNORECASE
    ),
}

# Patterns indicating a claim/assertion (not a question, example, or reference)
_ASSERTION_PATTERNS = {
    "en": [
        re.compile(r'\b(is|are|must be|cannot be|is not)\b.*\b(the|a|an)\b', re.I),
        re.compile(r'\b(all|every|no|each)\b.*\b(is|are|must|have)\b', re.I),
        re.compile(r'\b(nothing|everything|something)\b.*\b(is|exists|can)\b', re.I),
        re.compile(r'\bthere (is|exists|can be) no\b', re.I),
        re.compile(r'\b(we must|one must|one ought|it is necessary)\b', re.I),
        re.compile(r'\bthe (essence|nature|ground|source|origin) of\b', re.I),
    ],
    "ja": [
        re.compile(r'(である|でなければならない|にほかならない|ことはできない|なければならない)'),
        re.compile(r'(すべて|あらゆる|いかなる|つねに).*(である|ではない|にある)'),
        re.compile(r'(本質|根本|根源|究極).*(は|とは|にある|である)'),
        re.compile(r'.*(とは|は).*(である|にある|ことである|ものである)'),
        re.compile(r'(的である|的にある|においてこそ)'),
    ],
    "zh": [
        re.compile(r'(也|矣|乎|哉)$'),
        re.compile(r'(者|之|所以|故|則)'),
    ],
}

# Patterns that DISQUALIFY a sentence as a thesis
_EXCLUSION_PATTERNS = {
    "en": [
        re.compile(r'^\s*(For example|For instance|e\.g\.|i\.e\.)', re.I),
        re.compile(r'^\s*(In chapter|In section|As (we|I) (saw|noted|said))', re.I),
        re.compile(r'^\s*(He|She|They|Plato|Aristotle|Kant|Hume)\s+(said|argued|wrote|claimed|believed|thought)', re.I),
        re.compile(r'\b(pp?\.\s*\d|vol\.\s*\d|ch\.\s*\d|footnote|ibid)\b', re.I),
        re.compile(r'^\s*(But|However|On the other hand|Nevertheless)\s*,?\s*$', re.I),
        re.compile(r'^\s*\d+\.\s'),  # Numbered lists
        re.compile(r'^\s*\('),       # Parenthetical
    ],
    "ja": [
        re.compile(r'(例えば|たとえば|第\d+章|注\d+)'),
        re.compile(r'(と述べている|と論じた|によれば)'),
    ],
    "zh": [],
}


class ThesisExtractor:
    """Extract philosophical theses from text.

    A thesis is a philosophical claim that:
    1. Contains philosophical vocabulary (being, knowledge, virtue, etc.)
    2. Makes an assertion (not a question, example, or reference)
    3. Has sufficient generality (not about a specific person/event)
    4. Is substantive (not a mere transition or bibliographic note)

    Usage:
        extractor = ThesisExtractor(language="en")
        theses = extractor.extract(text)
        for t in theses:
            print(f"[{t.thesis_type}] {t.text}")

    The extracted theses can then be fed to SchoolClassifier for
    school identification.
    """

    def __init__(
        self,
        language: str = "en",
        min_philosophical_terms: int = 2,
        min_length: int = 30,
        max_length: int = 500,
    ):
        self.language = language
        self.min_terms = min_philosophical_terms
        self.min_length = min_length
        self.max_length = max_length
        # CJK languages have shorter sentences
        if language in ("ja", "zh") and min_length == 30:
            self.min_length = 10
        self._phil_re = _PHILOSOPHICAL_TERMS.get(language, _PHILOSOPHICAL_TERMS["en"])
        self._assert_pats = _ASSERTION_PATTERNS.get(language, [])
        self._exclude_pats = _EXCLUSION_PATTERNS.get(language, [])

    def extract(self, text: str) -> list[Thesis]:
        """Extract philosophical theses from a text passage."""
        sentences = self._split_sentences(text)
        theses = []
        for sent in sentences:
            score, thesis_type = self._score_sentence(sent)
            if score > 0:
                theses.append(Thesis(
                    text=sent.strip(),
                    thesis_type=thesis_type,
                    confidence=min(score / 5.0, 1.0),
                    source_paragraph=text[:200],
                    language=self.language,
                    is_negation=self._is_negation(sent),
                    universality=self._universality(sent),
                ))
        # Sort by confidence descending
        theses.sort(key=lambda t: t.confidence, reverse=True)
        return theses

    def extract_from_paragraphs(
        self, paragraphs: list[str], top_k: int = 20
    ) -> list[Thesis]:
        """Extract theses from multiple paragraphs, return top-k."""
        all_theses = []
        for para in paragraphs:
            all_theses.extend(self.extract(para))
        # Deduplicate by text similarity
        unique = []
        seen_texts: set[str] = set()
        for t in sorted(all_theses, key=lambda x: x.confidence, reverse=True):
            normalized = t.text.lower().strip()[:50]
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                unique.append(t)
        return unique[:top_k]

    def _score_sentence(self, sent: str) -> tuple[float, ThesisType | None]:
        """Score a sentence for thesis-likeness. Returns (score, type)."""
        sent = sent.strip()

        # Length check
        if len(sent) < self.min_length or len(sent) > self.max_length:
            return 0.0, None

        # Exclusion check
        for pat in self._exclude_pats:
            if pat.search(sent):
                return 0.0, None

        score = 0.0

        # Philosophical vocabulary density
        phil_matches = self._phil_re.findall(sent)
        n_phil = len(phil_matches)
        if n_phil < self.min_terms:
            return 0.0, None
        score += min(n_phil, 5)  # Cap at 5

        # Assertion pattern match
        for pat in self._assert_pats:
            if pat.search(sent):
                score += 1.5
                break

        # Universality boost (all, every, nothing, etc.)
        if re.search(r'\b(all|every|no|nothing|always|never|necessarily|impossible)\b',
                     sent, re.I):
            score += 1.0

        # Definitional pattern ("X is Y", "X consists in Y")
        if re.search(r'\b\w+\s+(is|are|consists in|amounts to)\s+(the|a|an|not)\b',
                     sent, re.I):
            score += 1.0

        # Determine thesis type
        thesis_type = self._classify_type(sent, phil_matches)

        return score, thesis_type

    def _classify_type(
        self, sent: str, phil_terms: list[str]
    ) -> ThesisType | None:
        """Classify the type of philosophical thesis."""
        sent_lower = sent.lower()
        terms = {t.lower() for t in phil_terms}

        if terms & {"being", "existence", "substance", "reality", "essence",
                     "存在", "本質", "実在", "有", "無"}:
            return ThesisType.ONTOLOGICAL
        if terms & {"knowledge", "truth", "reason", "perception", "experience",
                     "understanding", "知識", "認識", "真理", "理性", "経験"}:
            return ThesisType.EPISTEMOLOGICAL
        if terms & {"duty", "virtue", "justice", "good", "evil", "moral", "ethical",
                     "義務", "徳", "正義", "善", "悪", "仁", "義"}:
            return ThesisType.ETHICAL
        if terms & {"cause", "infinite", "absolute", "necessary", "soul", "spirit",
                     "原因", "絶対", "精神", "魂", "無限", "理", "気", "道"}:
            return ThesisType.METAPHYSICAL
        if terms & {"beauty", "美", "aesthetic"}:
            return ThesisType.AESTHETIC
        if terms & {"freedom", "will", "meaning", "自由", "意志", "意味"}:
            return ThesisType.EXISTENTIAL
        if terms & {"justice", "rights", "governance", "正義", "天下"}:
            return ThesisType.POLITICAL
        return None

    @staticmethod
    def _is_negation(sent: str) -> bool:
        return bool(re.search(
            r'\b(not|no|never|neither|nor|cannot|impossible|ない|非|無|不)\b',
            sent, re.I
        ))

    @staticmethod
    def _universality(sent: str) -> float:
        """Estimate how universal (vs particular) a claim is."""
        universal = len(re.findall(
            r'\b(all|every|always|necessarily|universal|must|any|'
            r'すべて|あらゆる|必然|常に|万物)\b', sent, re.I
        ))
        particular = len(re.findall(
            r'\b(this|that|here|now|sometimes|perhaps|'
            r'この|その|ここ|今|時には)\b', sent, re.I
        ))
        total = universal + particular
        if total == 0:
            return 0.5
        return universal / total

    def _split_sentences(self, text: str) -> list[str]:
        if self.language in ("ja",):
            return [s.strip() for s in re.split(r'[。！？]', text) if s.strip()]
        elif self.language in ("zh",):
            return [s.strip() for s in re.split(r'[。！？；]', text) if s.strip()]
        else:
            return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
