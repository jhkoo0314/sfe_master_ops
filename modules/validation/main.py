"""
Bridge entrypoint for the Validation Layer (OPS) API.

This keeps the current FastAPI app wired through `ops_core.main`
while new code can start importing `modules.validation.main`.
"""

from ops_core.main import app

__all__ = ["app"]
