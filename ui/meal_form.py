"""Hero and meal-planning input form for the Streamlit app."""

from typing import Any

import streamlit as st

from utils.formatting import parse_ingredients, remove_ingredient_from_input


DEFAULT_INGREDIENTS = (
    "extra-virgin olive oil, whole grains, fresh fruits and vegetables, "
    "nuts and seeds, fish, eggs, fermented foods, honey"
)


def remove_ingredient_chip(ingredient_to_remove: str) -> None:
    """Update the ingredient text area after a chip remove button is clicked."""
    current_value = st.session_state.get("ingredients_input", "")
    st.session_state["ingredients_input"] = remove_ingredient_from_input(
        current_value,
        ingredient_to_remove,
    )


def render_hero() -> None:
    """Render the top hero section."""
    st.markdown(
        """
        <div class="hero-grid">
          <div class="hero-copy">
            <p class="eyebrow">✨ AI Meal Planner</p>
            <h1 class="hero-title">Plan a full day of meals in seconds.</h1>
            <p class="hero-subtitle">
              Get personalized breakfast, lunch, and dinner ideas using the ingredients you love.
            </p>
          </div>
          <div class="food-orb"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_meal_form() -> dict[str, Any]:
    """Render ingredient, preference, narration, and generate controls."""
    input_col, cta_col = st.columns([4.3, 1.25], gap="large")

    if "ingredients_input" not in st.session_state:
        st.session_state["ingredients_input"] = DEFAULT_INGREDIENTS

    with input_col:
        with st.container(key="planner_card"):
            form_col_left, form_col_right = st.columns([1.75, 1], gap="large")

            with form_col_left:
                st.markdown('<div class="section-label">🌿 Base Ingredients</div>', unsafe_allow_html=True)
                ingredients = st.text_area(
                    label="Ingredients",
                    label_visibility="collapsed",
                    key="ingredients_input",
                    height=118,
                    placeholder="e.g. chicken, broccoli, quinoa, lemon, garlic ...",
                )

                ingredient_items = parse_ingredients(ingredients)
                visible_ingredients = ingredient_items[:5]
                hidden_ingredients = max(len(ingredient_items) - len(visible_ingredients), 0)

                if ingredient_items:
                    with st.container(key="ingredient_chips", horizontal=True, gap="small"):
                        for index, ingredient in enumerate(visible_ingredients):
                            safe_key_part = "".join(
                                char if char.isalnum() else "_"
                                for char in ingredient.lower()
                            )
                            st.button(
                                f"{ingredient} ×",
                                key=f"remove_ingredient_{index}_{safe_key_part}",
                                on_click=remove_ingredient_chip,
                                args=(ingredient,),
                            )
                        if hidden_ingredients:
                            st.markdown(
                                f'<span class="chip chip-muted">+{hidden_ingredients} more</span>',
                                unsafe_allow_html=True,
                            )

            with form_col_right:
                st.markdown(
                    '<div class="section-label">🧾 Extra Notes <span class="optional">(optional)</span></div>',
                    unsafe_allow_html=True,
                )
                extra = st.text_input(
                    label="Extra notes",
                    label_visibility="collapsed",
                    placeholder="e.g. spicy, low-carb, no sugar ...",
                )

                st.markdown(
                    '<div class="section-label" style="margin-top:1.18rem;">🛡️ Dietary Restriction <span class="optional">(optional)</span></div>',
                    unsafe_allow_html=True,
                )
                diet = st.text_input(
                    label="Dietary restriction",
                    label_visibility="collapsed",
                    placeholder="e.g. vegan, gluten-free, dairy-free ...",
                )

            st.markdown('<div class="planner-divider"></div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-label">🔊 Audio Narration <span class="optional">— select meals to narrate</span></div>',
                unsafe_allow_html=True,
            )

            with st.container(key="narration_controls"):
                narration_cols = st.columns([0.95, 0.95, 0.95, 1.28, 1.28], gap="small")

                with narration_cols[0]:
                    narrate_breakfast = st.checkbox("🌅 Breakfast", value=True)
                with narration_cols[1]:
                    narrate_lunch = st.checkbox("☀️ Lunch", value=True)
                with narration_cols[2]:
                    narrate_dinner = st.checkbox("🌙 Dinner", value=True)

                any_narration = narrate_breakfast or narrate_lunch or narrate_dinner

                with narration_cols[3]:
                    if any_narration:
                        tts_voice = st.selectbox(
                            "Voice",
                            ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                            index=0,
                        )
                    else:
                        tts_voice = "alloy"
                        st.selectbox(
                            "Voice",
                            ["alloy"],
                            index=0,
                            disabled=True,
                        )

                with narration_cols[4]:
                    if any_narration:
                        tts_quality = st.selectbox(
                            "Quality",
                            ["tts-1", "tts-1-hd"],
                            index=0,
                            format_func=lambda value: {
                                "tts-1": "Standard",
                                "tts-1-hd": "High",
                            }.get(value, value),
                        )
                    else:
                        tts_quality = "tts-1"
                        st.selectbox(
                            "Quality",
                            ["tts-1"],
                            index=0,
                            disabled=True,
                            format_func=lambda value: "Standard",
                        )

    with cta_col:
        with st.container(key="cta_panel"):
            generate_btn = st.button("✨ Generate Meal Plan", use_container_width=True)
            st.markdown(
                '<div class="cta-hint">It only takes a few seconds</div><div class="cta-arrow">↗</div>',
                unsafe_allow_html=True,
            )

    narrate_keys: list[str] = []
    if narrate_breakfast:
        narrate_keys.append("breakfast")
    if narrate_lunch:
        narrate_keys.append("lunch")
    if narrate_dinner:
        narrate_keys.append("dinner")

    return {
        "ingredients": ingredients,
        "extra": extra,
        "diet": diet,
        "tts_voice": tts_voice,
        "tts_quality": tts_quality,
        "narrate_keys": narrate_keys,
        "generate_btn": generate_btn,
    }
