"""Phil Workbench - Integrated interface for computational philosophy."""
from philbench.verbs import read, embed, search, compare, explore, annotate, quantify
from philbench.pipeline import PhilPipeline

__all__ = ["read", "embed", "search", "compare", "explore", "annotate",
           "quantify", "PhilPipeline"]
