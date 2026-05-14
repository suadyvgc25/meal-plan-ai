"""
meal_logic.py — Business logic for the Daily Meal Planner.
All OpenAI API interactions live here; no Streamlit imports.
"""

import os
import requests
import shutil
from pathlib import Path
from openai import OpenAI


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client() -> OpenAI:
    """Return an OpenAI client, reading the key from the environment."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key)


def _parse_titles(raw_output: str) -> list[str]:
    """
    Extract meal titles from the last non-empty, non-fence line of the LLM output.

    The prompt instructs the model to end with a comma-separated title string.
    """
    lines = [l.strip() for l in raw_output.splitlines() if l.strip()]
    # Walk backwards to find the titles line (skip ``` fences)
    for line in reversed(lines):
        if line.startswith("```") or not line:
            continue
        # Strip surrounding quotes/backticks
        cleaned = line.strip("'\"` ")
        titles = [t.strip(" '\"") for t in cleaned.split(",")]
        if len(titles) >= 2:          # sanity check: we expect at least 2 meals
            return titles
    return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_meal_plan(
    ingredients: str,
    kcal: int = 2000,
    exact_ingredients: bool = False,
    extra: str | None = None,
    model: str = "gpt-3.5-turbo",
    temperature: float = 1.0,
) -> tuple[str, list[str]]:
    """
    Generate a daily meal plan (HTML) and return (html_string, [meal_titles]).

    Parameters
    ----------
    ingredients : str
        Comma-separated list of base ingredients.
    kcal : int
        Maximum total daily calorie target.
    exact_ingredients : bool
        If True, only the provided ingredients may be used.
    extra : str | None
        Optional additional style/dietary instruction (e.g. "spicy").
    model : str
        OpenAI chat model to use.
    temperature : float
        Sampling temperature.

    Returns
    -------
    html : str
        Full HTML markup of the meal plan.
    titles : list[str]
        Recipe titles extracted from the response (used for image generation).
    """
    client = _get_client()

    ingredient_instruction = (
        "use ONLY the provided ingredients with salt, pepper, and spices."
        if exact_ingredients
        else (
            "Feel free to incorporate the provided ingredients as a base and add "
            "other ingredients if you consider them necessary to enhance the flavour, "
            "nutritional value, or overall appeal of the recipes."
        )
    )

    extra_instruction = f"8. If possible the meals should be: {extra}" if extra else ""

    prompt = f"""
Create a healthy daily meal plan for breakfast, lunch, and dinner based on the
following ingredients: ```{ingredients}```

Your output should be in the HTML and CSS format.
Follow the instructions below carefully.

### Instructions:
1. {ingredient_instruction}
2. Specify the exact amount of each ingredient.
3. Ensure that the total daily calorie intake is below {kcal}.
4. For each meal, explain each recipe step by step in clear and simple sentences.
   Use bullet points or numbers to organise the steps.
5. For each meal, specify the total number of calories and the number of servings.
6. For each meal, provide a concise and descriptive title that summarises the main
   ingredients and flavours. The title should also be a valid Dall-E prompt to
   generate an original image for the meal.
7. For each recipe, indicate the prep, cook, and total time.
{extra_instruction}

Before answering, make sure that you have followed all instructions.
The LAST line of your answer must contain ONLY the recipe titles separated by commas.
Example last line:
'Broccoli and Egg Scramble, Grilled Chicken and Vegetable, Baked Fish with Cabbage Slaw'
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a skilled cook with the expertise of a chef.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )

    raw = response.choices[0].message.content

    # Strip leading/trailing code fences if the model wrapped the HTML
    html = raw
    if html.strip().startswith("```"):
        lines = html.strip().splitlines()
        html = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    titles = _parse_titles(raw)
    return html, titles


def generate_meal_image(
    title: str,
    save_dir: str = ".",
    extra: str = "white background, food photography",
    model: str = "dall-e-3",
    size: str = "1024x1024",
    quality: str = "standard",
) -> str | None:
    """
    Generate a DALL-E image for *title* and save it to *save_dir*.

    Returns the local file path on success, or None on failure.
    """
    client = _get_client()

    image_prompt = f"{title}, hd quality, {extra}"

    response = client.images.generate(
        model=model,
        prompt=image_prompt,
        style="natural",
        size=size,
        quality=quality,
    )

    image_url = response.data[0].url
    image_resource = requests.get(image_url, stream=True)

    if image_resource.status_code != 200:
        return None

    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
    filename = Path(save_dir) / f"{safe_name}.png"
    filename.parent.mkdir(parents=True, exist_ok=True)

    with open(filename, "wb") as f:
        shutil.copyfileobj(image_resource.raw, f)

    return str(filename)
