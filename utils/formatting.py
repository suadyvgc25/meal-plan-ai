"""Formatting, parsing, and asset helpers for the meal planner UI."""

import base64
import html
from pathlib import Path
from typing import Any

import streamlit as st


def safe_text(value: Any, fallback: str = "") -> str:
    """Convert any value to display text."""
    if value is None:
        return fallback
    return str(value).strip() or fallback


def escape(value: Any, fallback: str = "") -> str:
    """Escape text before placing it inside custom HTML."""
    return html.escape(safe_text(value, fallback))


def as_list(value: Any) -> list[str]:
    """Normalize strings/lists/dicts into a simple list of strings for display."""
    if value is None:
        return []

    if isinstance(value, list):
        return [safe_text(item) for item in value if safe_text(item)]

    if isinstance(value, tuple):
        return [safe_text(item) for item in value if safe_text(item)]

    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            key_text = safe_text(key)
            item_text = safe_text(item)
            if key_text and item_text:
                items.append(f"{key_text}: {item_text}")
            elif item_text:
                items.append(item_text)
        return items

    text = safe_text(value)
    if not text:
        return []

    lines = [line.strip(" •-*") for line in text.splitlines() if line.strip(" •-*")]
    if len(lines) > 1:
        return lines

    comma_items = [item.strip() for item in text.split(",") if item.strip()]
    return comma_items if len(comma_items) > 1 else [text]


def get_meal_value(meal: dict[str, Any], possible_keys: list[str], fallback: Any = None) -> Any:
    """Read a value from a meal dict using several possible key names."""
    for key in possible_keys:
        if key in meal and meal[key] not in (None, ""):
            return meal[key]
    return fallback


def get_meal_title(key: str, meal: dict[str, Any], titles: list[str]) -> str:
    """Return the best title for a meal card."""
    default_titles = {
        "breakfast": "Breakfast",
        "lunch": "Lunch",
        "dinner": "Dinner",
    }

    title = get_meal_value(meal, ["title", "name", "meal_title"], "")
    if title:
        return safe_text(title)

    index_by_key = {"breakfast": 0, "lunch": 1, "dinner": 2}
    index = index_by_key.get(key)
    if index is not None and index < len(titles):
        return safe_text(titles[index], default_titles.get(key, "Meal"))

    return default_titles.get(key, "Meal")


def get_meal_calories(meal: dict[str, Any]) -> str:
    """Return a normalized calorie label for a meal."""
    calories = get_meal_value(meal, ["calories", "kcal", "estimated_calories"], "")
    if not calories:
        return ""
    calories_text = safe_text(calories)
    return calories_text if "cal" in calories_text.lower() else f"{calories_text} kcal"


def parse_ingredients(raw_ingredients: str) -> list[str]:
    """Split the comma-separated ingredient field into clean chip labels."""
    return [item.strip() for item in raw_ingredients.split(",") if item.strip()]


def remove_ingredient_from_input(raw_ingredients: str, ingredient_to_remove: str) -> str:
    """Remove one ingredient chip from the comma-separated input text."""
    remaining = [
        item for item in parse_ingredients(raw_ingredients)
        if item != ingredient_to_remove
    ]
    return ", ".join(remaining)


def render_compact_bullets(items: list[str], max_items: int = 5) -> str:
    """Create compact bullet HTML for result cards."""
    if not items:
        return "<ul><li>No details returned.</li></ul>"
    shown = items[:max_items]
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in shown) + "</ul>"


def meal_icon(key: str) -> str:
    """Return the display icon for a meal key."""
    return {
        "breakfast": "🌅",
        "lunch": "☀️",
        "dinner": "🌙",
    }.get(key, "🍽️")


def meal_label(key: str) -> str:
    """Return the display label for a meal key."""
    return {
        "breakfast": "Breakfast",
        "lunch": "Lunch",
        "dinner": "Dinner",
    }.get(key, "Meal")


def meal_keys_from_data(meals: dict[str, Any]) -> list[str]:
    """Prefer breakfast/lunch/dinner order, then append any extra meal keys."""
    standard = ["breakfast", "lunch", "dinner"]
    found = [key for key in standard if key in meals]
    extras = [key for key in meals.keys() if key not in standard]
    return found + extras


def image_data_uri(image_bytes: bytes | None) -> str:
    """Convert generated image bytes into an embeddable data URI."""
    if not image_bytes:
        return ""
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def local_image_data_uri(path: str) -> str:
    """Convert a local image asset into an embeddable data URI."""
    image_path = Path(path)
    if not image_path.exists():
        return ""
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def load_css(path: str) -> None:
    """Load a CSS file into the Streamlit page."""
    css_path = Path(path)
    if not css_path.exists():
        return
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
