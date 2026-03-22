"""
Primary Validation / Orchestration module path for Sales Data OS.

New code should import from `modules.validation`.
During migration, this package still re-exports the current `ops_core`
implementation so runtime stability is preserved.
"""

from .main import app

__all__ = ["app"]
