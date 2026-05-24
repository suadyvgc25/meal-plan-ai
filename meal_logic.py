"""
meal_logic.py — Business logic for the Daily Meal Planner.
All OpenAI API interactions live here; no Streamlit imports.
"""

import base64
import json
import os
import re
from pathlib import Path
from openai import OpenAI


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key)


def generate_meal_plan(
    ingredients: str,
    kcal: int = 2000,
    exact_ingredients: bool = False,
    extra: str | None = None,
    diet: str | None = None,
    model: str = "gpt-4o-mini",
    temperature: float = 1.0,
) -> tuple[list[str], dict]:
    """
    Generate a daily meal plan and return (recipe_titles, meals).

    Returns
    -------
    titles : list[str]  ["Breakfast title", "Lunch title", "Dinner title"]
    meals : dict        {"breakfast": {title, calories, ingredients, instructions}, ...}
    """
    client = _get_client()

    ingredient_instruction = (
        "Use ONLY the provided ingredients with salt, pepper, and spices."
        if exact_ingredients
        else (
            "Feel free to incorporate the provided ingredients as a base and add "
            "other ingredients if you consider them necessary to enhance the flavor, "
            "nutritional value, or overall appeal of the recipes."
        )
    )

    extra_line = f"8. If possible the meals should be: {extra}" if extra else ""
    diet_line  = (
        f"9. Dietary restriction: The meals must follow this diet: {diet}. "
        "If the provided ingredients conflict with the dietary restriction, "
        "replace them with appropriate alternatives and explain the substitutions inside the recipe."
        if diet else ""
    )

    prompt = f"""
Create a healthy daily meal plan for breakfast, lunch, and dinner based on the
following ingredients: ```{ingredients}```
Return the meal plan as structured JSON.
Follow the instructions below carefully.

### Instructions:
1. {ingredient_instruction}
2. Specify the exact amount of each ingredient.
3. Ensure that the total daily calorie intake is below {kcal}.
4. For each meal, explain each recipe step by step in clear and simple sentences.
   Use bullet points or numbers to organize the steps.
5. For each meal, specify the total number of calories and the number of servings.
6. For each meal, provide a concise and descriptive title that summarizes the main
   ingredients and flavors. The title should also be a good image-generation prompt.
7. For each recipe, indicate the prep, cook, and total time.
{extra_line}
{diet_line}
If a dietary restriction is provided, do not include ingredients that violate it.

Return ONLY valid JSON in this exact format:
{{
  "meals": {{
    "breakfast": {{
      "title": "Breakfast recipe title",
      "calories": "520 kcal",
      "ingredients": ["Ingredient 1", "Ingredient 2"],
      "instructions": ["Step 1", "Step 2", "Step 3"]
    }},
    "lunch": {{
      "title": "Lunch recipe title",
      "calories": "680 kcal",
      "ingredients": ["Ingredient 1", "Ingredient 2"],
      "instructions": ["Step 1", "Step 2", "Step 3"]
    }},
    "dinner": {{
      "title": "Dinner recipe title",
      "calories": "630 kcal",
      "ingredients": ["Ingredient 1", "Ingredient 2"],
      "instructions": ["Step 1", "Step 2", "Step 3"]
    }}
  }}
}}

Do not wrap the JSON in ```json.
Do not wrap the JSON in markdown code fences.
Do not include explanations outside the JSON.
The "instructions" arrays must contain the actual step-by-step cooking instructions — not placeholders.
Write everything out in full.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a skilled cook with the expertise of a chef. "
                    "Always return complete, fully written recipes. "
                    "Never use placeholder text."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=3000,
    )

    raw = response.choices[0].message.content.strip()

    # Strip accidental markdown fences if the model disobeys
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    data = json.loads(raw)
    meals = data.get("meals", {})
    meal_order = ["breakfast", "lunch", "dinner"]
    recipe_titles = [
        str(meals[key].get("title", "")).strip()
        for key in meal_order
        if isinstance(meals.get(key), dict) and meals[key].get("title")
    ]

    return recipe_titles, meals


def generate_meal_image(
    title: str,
    save_dir: str = ".",
    extra: str = "white background, food photography",
    model: str = "gpt-image-1",
    size: str = "1024x1024",
    quality: str = "low",
) -> bytes | None:
    """
    Generate an image using gpt-image-1 (base64, no URL, no 'style' param).
    Returns raw PNG bytes on success, or None on failure.
    """
    client = _get_client()

    response = client.images.generate(
        model=model,
        prompt=f"{title}, realistic natural food photography, hd quality, {extra}",
        size=size,
        quality=quality,
    )

    image_base64 = response.data[0].b64_json
    if not image_base64:
        return None

    image_bytes = base64.b64decode(image_base64)

    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", title).strip("_")
    filename  = Path(save_dir) / f"{safe_name}.png"
    filename.parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "wb") as f:
        f.write(image_bytes)

    return image_bytes


def speak_narration(
    narration_script: str,
    voice: str = "alloy",
    model: str = "tts-1",
) -> bytes | None:
    """
    Convert a narration script to MP3 audio using OpenAI TTS.

    The app builds this script from the structured meal title, ingredients,
    and instructions before calling this function.

    Parameters
    ----------
    narration_script : str   Plain text spoken script.
    voice : str              alloy | echo | fable | onyx | nova | shimmer
    model : str              tts-1 (fast) or tts-1-hd (higher quality)

    Returns
    -------
    bytes | None   Raw MP3 bytes, or None on failure.
    """
    client = _get_client()

    tts_response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=narration_script,
    )

    audio_bytes = tts_response.read()
    return audio_bytes if audio_bytes else None
