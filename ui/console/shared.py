"""얇게 남겨 둔 공통 표시 헬퍼.

실제 상태 관리, 경로 계산, 실행, 산출물 처리는
각각 전용 `ui.console_*` 모듈로 분리했다.
"""

from ui.console.display import (
    render_block_card,
    render_page_hero,
    render_panel_header,
    render_stage_badge,
    render_upload_row,
)

__all__ = [
    "render_block_card",
    "render_page_hero",
    "render_panel_header",
    "render_stage_badge",
    "render_upload_row",
]
