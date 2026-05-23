"""
app.py — Streamlit entry point for the Daily Meal Planner.

The app is intentionally split by responsibility:
- meal_logic.py handles OpenAI/business logic.
- ui/ modules render repeated Streamlit interface sections.
- utils/formatting.py holds reusable parsing, formatting, and asset helpers.
"""

import os
from pathlib import Path

import streamlit as st

from meal_logic import generate_meal_image, generate_meal_plan, speak_narration
from ui.meal_form import render_hero, render_meal_form
from ui.results import render_results
from ui.sidebar import render_sidebar
from utils.formatting import (
    build_downloadable_meal_plan_html,
    build_meal_narration_script,
    load_css,
    local_image_data_uri,
    meal_icon,
    meal_label,
)


st.set_page_config(
    page_title="Daily Meal Planner",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)


BASE_DIR = Path(__file__).resolve().parent
HERO_BG_URI = local_image_data_uri(BASE_DIR / "assets/images/hero-integrated-bg.png")


def load_dynamic_hero_background(hero_bg_uri: str) -> None:
    """Inject the hero background image after converting it to a data URI."""
    if not hero_bg_uri:
        return

    st.markdown(
        f"""
<style>
.block-container {{
  background:
    url("{hero_bg_uri}") top right / min(100%, 1160px) auto no-repeat,
    linear-gradient(180deg, rgba(252, 251, 244, 0.92) 0%, rgba(250, 250, 242, 0.86) 38%, rgba(247, 250, 244, 0.0) 72%) !important;
}}

.food-orb {{
  display: none !important;
}}

.food-orb::before,
.food-orb::after {{
  content: "" !important;
  display: none !important;
}}

.hero-copy {{
  position: relative;
  z-index: 1 !important;
  max-width: 760px;
}}

@media (min-width: 701px) and (max-width: 1100px) {{
  .block-container {{
    background:
      url("{hero_bg_uri}") top right / 940px auto no-repeat,
      linear-gradient(180deg, rgba(252, 251, 244, 0.92) 0%, rgba(250, 250, 242, 0.84) 38%, rgba(247, 250, 244, 0.0) 72%) !important;
  }}

  .hero-title,
  .hero-subtitle {{
    max-width: calc(100% - 270px) !important;
  }}
}}

@media (max-width: 700px) {{
  .block-container {{
    background: none !important;
  }}

  .food-orb {{
    display: none !important;
  }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


def configure_openai_key() -> None:
    """Load the OpenAI key from Streamlit secrets into the process environment."""
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]


def generate_current_plan(
    ingredients: str,
    kcal: int,
    exact_ingredients: bool,
    extra: str,
    diet: str,
    model_choice: str,
    temperature: float,
    narrate_keys: list[str],
    tts_voice: str,
    tts_quality: str,
) -> None:
    """Generate the meal plan and optional narration assets."""
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("Please add your OpenAI API Key under Settings → Secrets.")
        st.stop()

    if not ingredients.strip():
        st.warning("Please enter at least one ingredient.")
        st.stop()

    with st.spinner("Crafting your personalized meal plan…"):
        try:
            titles, meals = generate_meal_plan(
                ingredients=ingredients,
                kcal=kcal,
                exact_ingredients=exact_ingredients,
                extra=extra.strip() or None,
                diet=diet.strip() or None,
                model=model_choice,
                temperature=temperature,
            )
            html_output = build_downloadable_meal_plan_html(meals, kcal)

            st.session_state["html_output"] = html_output
            st.session_state["titles"] = titles
            st.session_state["meals"] = meals
            st.session_state["images"] = {}
            st.session_state["narrations"] = {}

        except Exception as exc:
            st.error(f"Error generating meal plan: {exc}")
            st.stop()

    generate_narrations(narrate_keys, tts_voice, tts_quality)


def generate_narrations(narrate_keys: list[str], tts_voice: str, tts_quality: str) -> None:
    """Generate MP3 narration for selected meals."""
    if not narrate_keys:
        return

    for key in narrate_keys:
        meal_data = st.session_state["meals"].get(key, {})
        script = build_meal_narration_script(key, meal_data)
        label = f"{meal_icon(key)} {meal_label(key)}"

        if not script:
            st.warning(f"No recipe steps returned for {label}.")
            continue

        with st.spinner(f"Generating {label} audio…"):
            try:
                audio_bytes = speak_narration(
                    narration_script=script,
                    voice=tts_voice,
                    model=tts_quality,
                )

                if audio_bytes:
                    st.session_state["narrations"][key] = audio_bytes
                else:
                    st.warning(f"No audio returned for {label}.")

            except Exception as exc:
                st.error(f"Audio error for {label}: {exc}")


configure_openai_key()
load_css(BASE_DIR / "styles/style.css")
load_dynamic_hero_background(HERO_BG_URI)

sidebar_values = render_sidebar()
render_hero()
form_values = render_meal_form()

if form_values["generate_btn"]:
    generate_current_plan(
        ingredients=form_values["ingredients"],
        kcal=sidebar_values["kcal"],
        exact_ingredients=sidebar_values["exact_ingredients"],
        extra=form_values["extra"],
        diet=form_values["diet"],
        model_choice=sidebar_values["model_choice"],
        temperature=sidebar_values["temperature"],
        narrate_keys=form_values["narrate_keys"],
        tts_voice=form_values["tts_voice"],
        tts_quality=form_values["tts_quality"],
    )

render_results(
    kcal=sidebar_values["kcal"],
    generate_images=sidebar_values["generate_images"],
    generate_meal_image=generate_meal_image,
)
