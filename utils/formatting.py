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


def build_downloadable_meal_plan_html(meals: dict[str, Any], kcal: int) -> str:
    """Build a standalone HTML meal plan from structured meal data."""
    keys = meal_keys_from_data(meals)
    meal_sections = []

    for key in keys:
        meal = meals.get(key, {})
        if not isinstance(meal, dict):
            meal = {"details": meal}

        title = get_meal_title(key, meal, [])
        calories = get_meal_calories(meal)
        ingredients = as_list(get_meal_value(meal, ["ingredients", "ingredient_list", "items"], ""))
        instructions = as_list(get_meal_value(meal, ["instructions", "steps", "method", "directions"], ""))

        ingredients_html = (
            "".join(f"<li>{escape(ingredient)}</li>" for ingredient in ingredients)
            if ingredients
            else "<li>No ingredients returned.</li>"
        )
        instructions_html = (
            "".join(f"<li>{escape(step)}</li>" for step in instructions)
            if instructions
            else "<li>No preparation steps returned.</li>"
        )
        calories_html = f'<span class="calories">{escape(calories)}</span>' if calories else ""

        meal_sections.append(
            f"""
            <article class="meal-card">
              <div class="meal-label">{escape(meal_icon(key))} {escape(meal_label(key))}</div>
              <h2>{escape(title)}</h2>
              {calories_html}
              <section>
                <h3>Ingredients</h3>
                <ul>{ingredients_html}</ul>
              </section>
              <section>
                <h3>Instructions</h3>
                <ol>{instructions_html}</ol>
              </section>
            </article>
            """
        )

    meal_count = len(keys) or 3
    rendered_meals = "\n".join(meal_sections) or "<p>No structured meal data was returned.</p>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Daily Meal Plan</title>
  <style>
    :root {{
      color-scheme: light;
      --green: #123f2c;
      --muted: #6d7972;
      --line: #dfe8df;
      --chip: #e9f2e5;
      --paper: #fffef9;
      --bg: #f8faf3;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #1f2f27;
      background: radial-gradient(circle at top right, #fff 0%, var(--bg) 42%, #f3f8ef 100%);
      line-height: 1.6;
    }}
    main {{
      width: min(1060px, calc(100% - 32px));
      margin: 0 auto;
      padding: 48px 0 64px;
    }}
    header {{
      margin-bottom: 28px;
    }}
    h1 {{
      margin: 0 0 8px;
      color: var(--green);
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(2rem, 5vw, 3.6rem);
      line-height: 1.05;
    }}
    .summary {{
      display: flex;
      align-items: center;
      gap: 14px;
      flex-wrap: wrap;
      color: #23362d;
      font-weight: 700;
    }}
    .tag,
    .calories {{
      display: inline-flex;
      align-items: center;
      width: fit-content;
      border-radius: 999px;
      background: var(--chip);
      color: var(--green);
      font-weight: 800;
      padding: 0.38rem 0.9rem;
    }}
    .meal-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 22px;
    }}
    .meal-card {{
      display: flex;
      flex-direction: column;
      gap: 16px;
      min-height: 100%;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.9);
      box-shadow: 0 20px 48px rgba(18, 63, 44, 0.08);
      padding: 24px;
    }}
    .meal-label {{
      align-self: flex-start;
      border-radius: 999px;
      background: var(--chip);
      color: var(--green);
      font-size: 0.82rem;
      font-weight: 900;
      letter-spacing: 0.08em;
      padding: 0.4rem 0.85rem;
      text-transform: uppercase;
    }}
    h2 {{
      margin: 0;
      color: var(--green);
      font-family: Georgia, "Times New Roman", serif;
      font-size: 1.85rem;
      line-height: 1.1;
    }}
    h3 {{
      margin: 0 0 8px;
      color: var(--green);
      font-size: 0.92rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    ul,
    ol {{
      margin: 0;
      padding-left: 1.25rem;
    }}
    li + li {{
      margin-top: 0.42rem;
    }}
    @media print {{
      body {{ background: #fff; }}
      main {{ width: 100%; padding: 24px; }}
      .meal-card {{ break-inside: avoid; box-shadow: none; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Healthy Daily Meal Plan</h1>
      <div class="summary">
        <span>{meal_count} meals • ~{escape(kcal)} kcal</span>
        <span class="tag">Balanced &amp; Nutritious</span>
      </div>
    </header>
    <section class="meal-grid">
      {rendered_meals}
    </section>
  </main>
</body>
</html>"""


def build_meal_narration_script(key: str, meal: dict[str, Any]) -> str:
    """Build a complete spoken recipe script from structured meal data."""
    title = safe_text(get_meal_value(meal, ["title", "name", "meal_title"], meal_label(key)))
    calories = get_meal_calories(meal)
    ingredients = as_list(get_meal_value(meal, ["ingredients", "ingredient_list", "items"], ""))
    instructions = as_list(get_meal_value(meal, ["instructions", "steps", "method", "directions"], ""))

    lines = [f"Here is how to prepare {title} for {meal_label(key).lower()}."]

    if calories:
        lines.append(f"This meal is approximately {calories}.")

    if ingredients:
        lines.append("You will need:")
        lines.extend(f"{index}. {ingredient}." for index, ingredient in enumerate(ingredients, start=1))

    if instructions:
        lines.append("Now, here are the preparation steps:")
        lines.extend(f"Step {index}. {step}" for index, step in enumerate(instructions, start=1))

    lines.append("Enjoy your meal.")
    return "\n".join(lines)


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


def local_image_data_uri(path: str | Path) -> str:
    """Convert a local image asset into an embeddable data URI."""
    image_path = Path(path)
    if not image_path.exists():
        return ""
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def load_css(path: str | Path) -> None:
    """Load a CSS file into the Streamlit page."""
    css_path = Path(path)
    if not css_path.exists():
        return
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
