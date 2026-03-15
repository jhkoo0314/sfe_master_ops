from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from ui.console_state import load_file_once


def render_page_hero(title: str, subtitle: str, badge: str | None = None) -> None:
    badge_html = f'<span class="app-badge">{badge}</span>' if badge else ""
    st.markdown(
        f"""
        <div class="page-hero">
          <div>
            <div class="hero-kicker">Sales Data OS Console</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
          <div>{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_panel_header(title: str, description: str = "") -> None:
    desc_html = f"<p>{description}</p>" if description else ""
    st.markdown(
        f"""
        <div class="panel-header">
          <h3>{title}</h3>
          {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_block_card(title: str, description: str, eyebrow: str = "") -> None:
    eyebrow_html = f'<div class="block-eyebrow">{eyebrow}</div>' if eyebrow else ""
    st.markdown(
        f"""
        <div class="block-card">
          {eyebrow_html}
          <h4>{title}</h4>
          <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upload_row(
    module_key: str,
    uploader_key: str,
    title: str,
    required_level: str,
    short_desc: str,
    sample_path: str,
    examples: list[str],
    notes: list[str],
    upload_label: str,
) -> None:
    level_colors = {
        "필수": ("rgba(248,81,73,0.10)", "#f85149"),
        "권장": ("rgba(210,153,34,0.12)", "#d29922"),
        "선택": ("rgba(88,166,255,0.10)", "#58a6ff"),
    }
    bg, fg = level_colors.get(required_level, ("rgba(139,148,158,0.16)", "#e6edf3"))
    current = st.session_state.uploaded_data.get(module_key)

    left, mid, right = st.columns([1.2, 2.4, 1.6])
    with left:
        st.markdown(
            f"""
            <div style="padding-top:6px">
              <div style="display:inline-flex;align-items:center;padding:4px 10px;border-radius:999px;background:{bg};color:{fg};font-size:11px;font-weight:800;margin-bottom:8px;">{required_level}</div>
              <div style="font-weight:800;font-size:15px;">{title}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with mid:
        status_text = f"업로드됨 · {current['name']} · {current['row_count']}건" if current else "업로드 전"
        st.markdown(
            f"""
            <div style="padding-top:6px">
              <div style="font-size:13px;font-weight:700;">{short_desc}</div>
              <div style="font-size:12px;color:#8b949e;margin-top:4px;">샘플: <code>{sample_path}</code></div>
              <div style="font-size:12px;color:#8b949e;margin-top:4px;">상태: {status_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("예시", expanded=False):
            for item in examples:
                st.markdown(f"- {item}")
            st.markdown("**체크 포인트**")
            for item in notes:
                st.markdown(f"- {item}")
    with right:
        uploaded_file = st.file_uploader(upload_label, type=["csv", "xlsx"], key=uploader_key, label_visibility="collapsed")
        if uploaded_file:
            try:
                info = load_file_once(module_key, uploaded_file, title)
                st.success(f"{info['row_count']}건")
            except Exception as exc:
                st.error(f"오류: {exc}")

    latest = st.session_state.uploaded_data.get(module_key)
    if latest:
        with st.expander(f"{title} 미리보기", expanded=False):
            st.dataframe(pd.DataFrame(latest["preview"]), use_container_width=True, hide_index=True)
    st.markdown("<div style='margin:8px 0 14px;border-top:1px solid rgba(48,54,61,0.8);'></div>", unsafe_allow_html=True)


def render_stage_badge(label: str, value: str) -> str:
    palette = {
        "정규화": ("rgba(88,166,255,0.10)", "#58a6ff"),
        "검증결과": ("rgba(63,185,80,0.10)", "#3fb950"),
        "Builder": ("rgba(210,153,34,0.12)", "#d29922"),
        "원천": ("rgba(248,81,73,0.10)", "#f85149"),
    }
    bg, fg = palette.get(label, ("rgba(139,148,158,0.16)", "#e6edf3"))
    return (
        f"<span style=\"display:inline-flex;align-items:center;padding:4px 10px;border-radius:999px;"
        f"background:{bg};color:{fg};font-size:11px;font-weight:800;margin-right:8px;\">"
        f"{label} · {value}</span>"
    )
