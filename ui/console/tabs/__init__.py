"""Console tab package."""

from ui.console.tabs.agent_tab import render_agent_tab
from ui.console.tabs.artifacts_tab import render_artifacts_tab
from ui.console.tabs.builder_tab import render_builder_tab
from ui.console.tabs.dashboard_tab import render_dashboard_tab
from ui.console.tabs.pipeline_tab import render_pipeline_tab
from ui.console.tabs.upload_tab import render_upload_tab

__all__ = [
    "render_agent_tab",
    "render_artifacts_tab",
    "render_builder_tab",
    "render_dashboard_tab",
    "render_pipeline_tab",
    "render_upload_tab",
]
