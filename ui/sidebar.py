"""Sidebar controls for the Daily Meal Planner app."""

from typing import Any

import streamlit as st


def render_sidebar() -> dict[str, Any]:
    """Render sidebar controls and return their current values."""
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
              <div class="sidebar-logo">🪴</div>
              <div>
                <p class="sidebar-title">Daily Meal Planner</p>
                <div class="sidebar-subtitle">AI-powered meal planning</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section-label">⚙ Settings</div>', unsafe_allow_html=True)

        kcal = st.number_input(
            "Daily calorie target (kcal)",
            min_value=800,
            max_value=5000,
            value=2000,
            step=50,
        )

        with st.container(
            key="exact_toggle_row",
            horizontal=True,
            horizontal_alignment="left",
            vertical_alignment="center",
            gap="small",
        ):
            st.markdown(
                '<div class="sidebar-control-label">Use ONLY listed ingredients</div>',
                unsafe_allow_html=True,
            )
            exact_ingredients = st.toggle(
                "Use ONLY listed ingredients",
                value=False,
                label_visibility="collapsed",
            )

        model_choice = st.selectbox(
            "Chat model",
            ["gpt-4o-mini", "gpt-4o"],
            index=0,
        )

        temperature = 1.0

        with st.container(
            key="image_toggle_row",
            horizontal=True,
            horizontal_alignment="left",
            vertical_alignment="center",
            gap="small",
        ):
            st.markdown(
                '<div class="sidebar-control-label">Generate dish images</div>',
                unsafe_allow_html=True,
            )
            generate_images = st.toggle(
                "Generate dish images",
                value=True,
                label_visibility="collapsed",
            )

        st.markdown(
            f"""
            <div class="tip-card">
              <div class="tip-row">
                <div class="tip-icon">🌿</div>
                <div><strong>Tip:</strong> The more specific your ingredients and notes are,
                the better your meal plan will be.</div>
              </div>
              <div class="kcal-card">
                <strong>🔥 {kcal} kcal target</strong><br>
                Balanced • Nutritious • Delicious
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "kcal": kcal,
        "exact_ingredients": exact_ingredients,
        "model_choice": model_choice,
        "temperature": temperature,
        "generate_images": generate_images,
    }
