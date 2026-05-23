# Daily Meal Planner

An AI-powered meal planning app that turns a list of ingredients into a full day of personalized meals, complete with recipe cards, calorie targets, generated dish images, and optional audio narration.

This project was built as a portfolio piece to demonstrate practical AI product design: prompt-driven structured generation, image generation, text-to-speech, Streamlit UI engineering, responsive layout work, and a polished visual system inspired by a high-fidelity design reference.

## Overview

Daily Meal Planner helps a user plan breakfast, lunch, and dinner from ingredients they already have. The user provides a calorie target, ingredients, optional preferences, and dietary restrictions. The app then generates a complete meal plan using OpenAI, displays the result in a custom-designed Streamlit interface, and can optionally generate realistic dish images and MP3 narration for selected meals.

The application focuses on making AI output feel usable, not just generated. The results are displayed as clean meal cards with structured ingredients, calorie information, generated images, and audio controls. Users can also download the full meal plan as HTML and download individual narration files as MP3s.

## Key Features

- AI-generated daily meal plan for breakfast, lunch, and dinner
- Calorie target control for the full day
- Base ingredient input with removable ingredient chips
- Optional extra notes for preferences such as low-carb, spicy, no sugar, and similar guidance
- Optional dietary restriction field
- Toggle to require the AI to use only listed ingredients
- Optional AI-generated dish images
- Optional audio narration for breakfast, lunch, and/or dinner
- In-card audio playback with native play, pause, and replay controls
- MP3 download for each narrated meal
- HTML download for the full generated meal plan
- Responsive layout for desktop, tablet, and mobile
- Custom visual styling to match a polished meal-planning product design

## Why This Project

This app explores a common real-world AI product challenge: turning a flexible natural-language model into a structured, user-friendly experience.

Instead of showing raw model output, the app asks the model for a predictable JSON structure, extracts the meal data, and renders it into an interface designed for scanning and action. The result is closer to a production product flow than a simple chatbot demo.

The project demonstrates:

- Prompt engineering for structured JSON responses
- Separation of business logic from UI code
- Handling model output safely enough for display
- AI image generation and text-to-speech integration
- Streamlit customization beyond default widgets
- Responsive UI refinement based on visual reference screenshots
- Downloadable generated artifacts

## Tech Stack

- Python
- Streamlit
- OpenAI Chat Completions API
- OpenAI Images API
- OpenAI Text-to-Speech API
- HTML/CSS inside Streamlit for custom layout and styling

## Project Structure

```text
meal-plan-ai/
├── app.py                       # Streamlit entry point and app orchestration
├── meal_logic.py                # OpenAI API calls and meal generation logic
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
├── assets/
│   └── images/
│       ├── hero-integrated-bg.png   # Integrated hero background artwork
│       └── hero-salad.png           # Salad image asset
├── styles/
│   └── style.css                # Custom CSS loaded by Streamlit
├── ui/
│   ├── sidebar.py               # Sidebar controls and settings
│   ├── meal_form.py             # Hero, ingredient inputs, narration controls, and CTA
│   └── results.py               # Generated meal cards, audio controls, and downloads
├── utils/
    └── formatting.py            # Shared formatting, parsing, and asset helpers
```

## Architecture

The app is intentionally split into focused modules:

| File | Responsibility |
| --- | --- |
| `app.py` | Main Streamlit entry point. Loads configuration, CSS, secrets, renders top-level sections, and coordinates generation. |
| `meal_logic.py` | Handles OpenAI calls for meal generation, dish image generation, and text-to-speech narration. It does not import Streamlit. |
| `ui/sidebar.py` | Renders sidebar settings such as calories, model choice, exact ingredient mode, and image generation. |
| `ui/meal_form.py` | Renders the hero section, ingredient form, preference inputs, narration controls, and generate button. |
| `ui/results.py` | Renders result headers, meal cards, images, audio controls, MP3 downloads, and the full HTML expander. |
| `utils/formatting.py` | Contains reusable helpers for text escaping, ingredient parsing, meal labels, calories, bullets, CSS loading, and image data URIs. |
| `styles/style.css` | Custom stylesheet loaded by Streamlit at runtime. |

This separation keeps the AI/business logic easier to understand and easier to reuse outside the UI.

## How It Works

1. The user enters ingredients, a calorie target, and optional preferences.
2. The app sends a structured prompt to OpenAI requesting JSON output.
3. The response includes:
   - Full rendered HTML
   - Recipe titles
   - Structured meal data for breakfast, lunch, and dinner
4. The app parses the structured response and stores the result in Streamlit session state.
5. If image generation is enabled, the app generates a food image for each meal.
6. If narration is selected, the app builds a spoken recipe script from each meal's title, ingredients, and instructions, then converts it into MP3 audio.
7. The UI renders the final result as custom meal cards with images, calories, ingredients, audio controls, and downloads.

## Setup

Clone the repository and install the dependencies:

```bash
pip install -r requirements.txt
```

Create a Streamlit secrets file:

```bash
mkdir -p .streamlit
touch .streamlit/secrets.toml
```

Add your OpenAI API key:

```toml
OPENAI_API_KEY = "your_api_key_here"
```

Run the app:

```bash
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

If port `8501` is already in use, Streamlit may use another port such as `8502`.

## Streamlit Theme

The app can use a Streamlit theme file at `.streamlit/config.toml`.

Example:

```toml
[theme]
primaryColor = "#123f2c"
```

This is safe to commit because it only controls visual styling. Do not commit `.streamlit/secrets.toml`.

## Styles

The custom interface styles live in the `styles/` folder.

Streamlit does not compile CSS. Instead, the app reads the stylesheet from disk and injects it into the page with `st.markdown`.

The app loads:

```text
styles/style.css
```

The helper function in `utils/formatting.py` is:

```python
def load_css(path: str) -> None:
    css_path = Path(path)
    if not css_path.exists():
        return
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
```

Because the app uses plain CSS, there is no separate compile step. Edit `styles/style.css`, save the file, and rerun or refresh the Streamlit app.

## Environment Variables and Secrets

The app expects an OpenAI API key named:

```text
OPENAI_API_KEY
```

In local Streamlit development, the recommended place is:

```text
.streamlit/secrets.toml
```

The `.gitignore` file excludes `.streamlit/secrets.toml` so private API keys are not committed.

## Using the App

1. Enter a daily calorie target.
2. Add ingredients in the Base Ingredients box.
3. Remove any ingredient chip by clicking the chip with the `x`.
4. Choose whether the meal plan must use only the listed ingredients.
5. Select a chat model.
6. Choose whether to generate dish images.
7. Add optional extra notes or dietary restrictions.
8. Select which meals should receive audio narration.
9. Click Generate Meal Plan.
10. Review the generated meal cards.
11. Play narration, download MP3 files, or download the full HTML plan.

## Design Notes

The visual direction is based on a warm, premium meal-planning interface:

- Deep green brand color
- Soft cream and sage backgrounds
- Rounded meal cards
- Realistic food imagery
- Compact, readable controls
- Sidebar settings panel
- Responsive card layouts
- Clear distinction between narrated and non-narrated meals

The UI was refined through several design passes to better match the provided reference screenshots, including sidebar spacing, toggle alignment, hero background integration, narration controls, and final meal card composition.

## Notable Implementation Details

- Ingredient chips update the original ingredient input, not only the visual chip list.
- Meal cards keep a consistent height whether or not narration is selected.
- Non-narrated meals display a styled message instead of empty controls.
- Narrated meals use native audio controls so users can play, pause, and replay.
- MP3 downloads use Streamlit's native download button for reliable file downloads.
- The creativity temperature control was removed from the UI and fixed internally to reduce user-facing errors.
- The full generated HTML is still available in an expandable section for transparency.

## Current Limitations

- Generated meal quality depends on the selected model and the clarity of the user's ingredients and notes.
- Image generation requires an OpenAI API key with image-generation access.
- Audio narration requires access to OpenAI text-to-speech models.
- The app is optimized as a portfolio/demo experience, not as a clinical nutrition tool.
- Calorie counts are AI-generated estimates and should not be treated as medical or dietary advice.

## Future Improvements

- Add saved meal plan history
- Add editable meal cards after generation
- Add grocery list export
- Add macro breakdowns for protein, carbs, and fat
- Add recipe regeneration per meal
- Add stricter nutrition validation
- Add user authentication for saved plans
- Add persistent storage with a database
- Add deployment instructions for Streamlit Community Cloud or another hosting platform

## Portfolio Highlights

This project is a good example of:

- Building an AI workflow around real user tasks
- Designing a structured output pipeline from a language model
- Combining text, image, and audio generation in one product
- Creating a polished UI inside Streamlit
- Iterating from screenshots and design references
- Handling generated artifacts such as HTML, images, and MP3 files

## Disclaimer

This app is for meal planning inspiration only. It does not provide medical, nutritional, or dietary advice. Users with allergies, medical conditions, or strict dietary requirements should verify ingredients and nutrition information independently.
