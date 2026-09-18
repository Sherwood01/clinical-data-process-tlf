"""
Clinical Data Process - ADaM to TLF AI Agent System

This module provides AI agents for automating the generation of CSR TLF reports
(Tables, Listings, Figures) from ADaM datasets.
"""

__version__ = "0.1.0"


def _lazy_import(name):
    """Lazy-import a submodule to avoid pulling in heavy dependencies at package init."""
    import importlib
    return importlib.import_module(f".{name}", __package__)


# Top-level aliases — lazily resolved so simple submodule imports (e.g. src.report)
# don't trigger the full agent/rag dependency chain (which requires langgraph etc.).
def __getattr__(name):
    lazy_map = {
        "OrchestratorAgent": ("agents", "OrchestratorAgent"),
        "SAPParserAgent": ("agents", "SAPParserAgent"),
        "MacroSelectorAgent": ("agents", "MacroSelectorAgent"),
        "CodeGeneratorAgent": ("agents", "CodeGeneratorAgent"),
        "MacroKnowledgeBase": ("rag", "MacroKnowledgeBase"),
        "ADaMMetaDataIndex": ("rag", "ADaMMetaDataIndex"),
        "RAGRetriever": ("rag", "RAGRetriever"),
    }
    if name in lazy_map:
        mod_name, attr_name = lazy_map[name]
        mod = _lazy_import(mod_name)
        return getattr(mod, attr_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
