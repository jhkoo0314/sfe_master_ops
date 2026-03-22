"""
Compatibility bridge for execution mode and step definitions.
"""

from ops_core.workflow.execution_registry import *  # noqa: F403
from ops_core.workflow.execution_registry import _get_step_registry  # noqa: F401
