# Daily Meal Planner — Streamlit App

A clean Streamlit conversion of the `daily_meal_plan.ipynb` notebook.

## Project structure

```
meal_planner/
├── app.py            ← Streamlit UI (all display / interaction code)
├── meal_logic.py     ← Business logic (OpenAI calls, parsing, image saving)
├── requirements.txt
└── README.md
```

### Why two files?

| File | Responsibility |
|------|---------------|
| `meal_logic.py` | Talks to OpenAI. No Streamlit imports. Fully testable in isolation. |
| `app.py` | Renders the UI. Calls functions from `meal_logic`. No raw API calls. |

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

## Usage

1. Paste your **OpenAI API Key** in the sidebar.
2. Edit the ingredient list and optional dietary notes.
3. Adjust settings (calorie target, model, temperature).
4. Click **Generate Meal Plan**.
5. Optionally enable **Generate dish images** to create a DALL-E 3 image for each meal.

## Bug fixes from the original notebook

| Original issue | Fix |
|---|---|
| `titles` was parsed from `output.splitlines()[-2]` which broke when the model wrapped output in ` ``` ` fences | `_parse_titles()` walks backwards through lines, skips fence lines, and validates that at least 2 comma-separated titles were found |
| `IndexError` on `titles[1]` when only one title (or zero) were parsed | Parsing robustness fix above; UI skips image generation gracefully if titles list is empty |
| Incomplete `for` loop at end of notebook | Replaced with a proper `st.columns` loop in the UI |
| API key hard-coded in notebook cell | Key entered via sidebar `st.text_input(type="password")` and stored in `os.environ` for the session only |
