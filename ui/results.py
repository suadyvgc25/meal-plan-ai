"""Generated meal plan result rendering."""

import os
import tempfile
from collections.abc import Callable
from typing import Any

import streamlit as st

from utils.formatting import (
    as_list,
    escape,
    get_meal_calories,
    get_meal_title,
    get_meal_value,
    image_data_uri,
    meal_icon,
    meal_keys_from_data,
    meal_label,
    render_compact_bullets,
)


ImageGenerator = Callable[..., bytes | None]


def render_results(kcal: int, generate_images: bool, generate_meal_image: ImageGenerator) -> None:
    """Render generated meal cards, downloads, and the full HTML expander."""
    if "html_output" not in st.session_state:
        return

    html_output = st.session_state["html_output"]
    titles = st.session_state.get("titles", [])
    meals = st.session_state.get("meals", {})

    st.session_state.setdefault("images", {})
    st.session_state.setdefault("narrations", {})

    keys = meal_keys_from_data(meals)

    header_col, action_col = st.columns([1.7, 0.45], gap="large")

    with header_col:
        st.markdown(
            f"""
            <div class="result-header">
              <div>
                <h4 class="result-title">✨ Your Personalized Meal Plan ✨</h4>
                <div class="result-summary">
                  <span>{len(keys) or 3} meals • ~{escape(kcal)} kcal</span>
                  <span class="tag">Balanced & Nutritious</span>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with action_col:
        with st.container(key="result_actions"):
            st.download_button(
                label="⬇ Download Plan",
                data=html_output,
                file_name="daily_meal_plan.html",
                mime="text/html",
                use_container_width=True,
                key="download_plan_top",
            )

    if not keys:
        st.warning("The meal plan was generated, but no meal card data was returned. Open the full HTML plan below.")
    else:
        _render_meal_cards(
            keys=keys,
            meals=meals,
            titles=titles,
            generate_images=generate_images,
            generate_meal_image=generate_meal_image,
        )

    st.markdown(
        '<p class="html-expander-note">Need the original generated HTML? Open the full rendered plan below.</p>',
        unsafe_allow_html=True,
    )

    with st.expander("📄 Full meal plan — rendered HTML", expanded=False):
        st.components.v1.html(html_output, height=900, scrolling=True)


def _render_meal_cards(
    keys: list[str],
    meals: dict[str, Any],
    titles: list[str],
    generate_images: bool,
    generate_meal_image: ImageGenerator,
) -> None:
    """Render the responsive meal-card grid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        meal_columns = st.columns(3, gap="medium")
        for index, key in enumerate(keys):
            with meal_columns[index % 3]:
                meal = meals.get(key, {})
                if not isinstance(meal, dict):
                    meal = {"details": meal}

                title = get_meal_title(key, meal, titles)
                calories = get_meal_calories(meal)
                ingredients_list = as_list(
                    get_meal_value(
                        meal,
                        ["ingredients", "ingredient_list", "items"],
                        "",
                    )
                )

                cached_image = st.session_state["images"].get(title)

                if generate_images and not cached_image:
                    if not os.environ.get("OPENAI_API_KEY"):
                        st.warning("Add your API key in Streamlit Secrets to generate images.")
                    else:
                        with st.spinner(f"Generating image for {title}..."):
                            try:
                                img_bytes = generate_meal_image(
                                    title=title,
                                    save_dir=tmpdir,
                                    extra=(
                                        "modern healthy food photography, top-down, "
                                        "natural light, white ceramic plate, clean cream background"
                                    ),
                                )
                                if img_bytes:
                                    st.session_state["images"][title] = img_bytes
                                    cached_image = img_bytes
                            except Exception as exc:
                                st.error(f"Image error for {title}: {exc}")

                _render_meal_card(
                    key=key,
                    index=index,
                    title=title,
                    calories=calories,
                    ingredients_list=ingredients_list,
                    cached_image=cached_image,
                )


def _render_meal_card(
    key: str,
    index: int,
    title: str,
    calories: str,
    ingredients_list: list[str],
    cached_image: bytes | None,
) -> None:
    """Render one meal card and its narration/download state."""
    image_uri = image_data_uri(cached_image)
    image_html = (
        f'<img src="{image_uri}" alt="{escape(title)}">'
        if image_uri
        else f'<div class="target-meal-fallback">{meal_icon(key)}</div>'
    )
    calories_html = f'<span class="calorie-pill">{escape(calories)}</span>' if calories else ""
    audio = st.session_state["narrations"].get(key)

    with st.container(key=f"meal_card_{key}_{index}"):
        st.html(
            '<div class="target-meal-card-layout">'
            '<div class="target-meal-label">'
            f'<span class="target-meal-label-icon">{meal_icon(key)}</span>'
            f'<span>{escape(meal_label(key))}</span>'
            '</div>'
            f'<h3 class="target-meal-title">{escape(title)}</h3>'
            f'<div class="target-meal-calories">{calories_html}</div>'
            '<div class="target-meal-media">'
            f'{image_html}'
            '</div>'
            '<div class="target-meal-content">'
            f'{render_compact_bullets(ingredients_list, max_items=5)}'
            '</div>'
            '</div>'
        )

        if audio:
            with st.container(key=f"meal_card_actions_{key}_{index}"):
                with st.container(key=f"meal_audio_player_{key}_{index}"):
                    st.audio(audio, format="audio/mp3")
                st.download_button(
                    label="⬇ Download MP3",
                    data=audio,
                    file_name=f"{key}_narration.mp3",
                    mime="audio/mp3",
                    key=f"download_audio_card_{key}_{index}",
                    use_container_width=True,
                )
        else:
            with st.container(key=f"meal_card_actions_{key}_{index}"):
                st.html(
                    '<div class="audio-empty">'
                    '<span class="audio-empty-icon">🌿</span>'
                    '<span>Audio narration not selected<br>for this meal.</span>'
                    '</div>'
                )
