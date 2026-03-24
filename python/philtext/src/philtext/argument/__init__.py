"""Argument extraction and analysis."""

from philtext.argument.schemas import Argument, Conclusion, InferenceType, Premise, Proposition
from philtext.argument.extractor import ArgumentExtractor
from philtext.argument.thesis import Thesis, ThesisExtractor, ThesisType

__all__ = [
    "Argument", "Conclusion", "InferenceType", "Premise", "Proposition",
    "ArgumentExtractor",
    "Thesis", "ThesisExtractor", "ThesisType",
]
