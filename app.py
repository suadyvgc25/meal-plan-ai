"""
app.py — Streamlit UI for the Daily Meal Planner.
All display / interaction code lives here.
Business logic is imported from meal_logic.py.
"""

import os
import tempfile
import streamlit as st

from meal_logic import generate_meal_plan, generate_meal_image, speak_narration

st.set_page_config(page_title="Daily Meal Planner", page_icon="🥗", layout="wide")

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; font-weight: 700; color: #1a3c2e; letter-spacing: -0.02em; margin-bottom: 0; }
    .subtitle { font-size: 1.05rem; color: #5a7a6a; font-weight: 300; margin-top: 0.25rem; margin-bottom: 2rem; }
    .section-label { font-size: 0.75rem; font-weight: 500; letter-spacing: 0.12em; text-transform: uppercase; color: #6b8f7e; margin-bottom: 0.4rem; }
    .stButton > button { background-color: #1a3c2e; color: #f0f7f4; border: none; border-radius: 6px; padding: 0.6rem 1.8rem; font-family: 'DM Sans', sans-serif; font-weight: 500; font-size: 0.95rem; letter-spacing: 0.03em; transition: background 0.2s; width: 100%; }
    .stButton > button:hover { background-color: #2d6b4a; }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stNumberInput > div > div > input { border-radius: 6px; border: 1.5px solid #d0e4da; font-family: 'DM Sans', sans-serif; }
    div[data-testid="stExpander"] { border: 1.5px solid #d0e4da; border-radius: 8px; }
    .tag { display: inline-block; background: #dff0e8; color: #1a3c2e; border-radius: 20px; padding: 0.2rem 0.75rem; font-size: 0.8rem; font-weight: 500; margin-right: 0.4rem; }
    .narration-box { background: #f7faf8; border-left: 4px solid #3d8b5e; border-radius: 0 8px 8px 0; padding: 1rem 1.25rem; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown('<p class="main-title">🥗 Daily Meal Planner</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Generate a personalised daily meal plan powered by AI — '
    "breakfast, lunch, and dinner in seconds.</p>",
    unsafe_allow_html=True,
)
st.divider()

# ---------------------------------------------------------------------------
# Sidebar — technical settings only (no narration toggle here anymore)
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ⚙️ Settings")

    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

    st.markdown("---")

    kcal = st.number_input("Daily calorie target (kcal)",
        min_value=800, max_value=5000, value=2000, step=50)

    exact_ingredients = st.toggle("Use ONLY listed ingredients", value=False,
        help="When on, the AI will not add any extra ingredients.")

    model_choice = st.selectbox("Chat model",
        ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"], index=2)

    temperature = st.slider("Creativity (temperature)",
        min_value=0.0, max_value=2.0, value=1.0, step=0.1)

    generate_images = st.toggle("Generate dish images", value=False,
        help="Generates one image per meal using gpt-image-1.")

    st.markdown("---")

# ---------------------------------------------------------------------------
# Main form — ingredients + options + narration selection all in one place
# ---------------------------------------------------------------------------

col_left, col_right = st.columns([2, 1], gap="large")

with col_left:
    st.markdown('<p class="section-label">Base Ingredients</p>', unsafe_allow_html=True)
    ingredients = st.text_area(
        label="Ingredients", label_visibility="collapsed",
        value=(
            "extra-virgin olive oil, whole grains, fresh fruits and vegetables, "
            "nuts and seeds, fish, eggs, fermented foods, honey"
        ),
        height=110,
        placeholder="e.g. chicken, broccoli, quinoa, lemon, garlic …",
    )

with col_right:
    st.markdown('<p class="section-label">Extra Notes (optional)</p>', unsafe_allow_html=True)
    extra = st.text_input(label="Extra notes", label_visibility="collapsed",
        placeholder="e.g. spicy, low-carb …")

    st.markdown('<p class="section-label" style="margin-top:0.75rem">Dietary Restriction (optional)</p>', unsafe_allow_html=True)
    diet = st.text_input(label="Diet", label_visibility="collapsed",
        placeholder="e.g. vegan, gluten-free …")

# ── Narration selection — below the two columns, above the button ─────────
st.markdown("---")
st.markdown('<p class="section-label">🔊 Audio Narration — select meals to narrate</p>', unsafe_allow_html=True)

narration_cols = st.columns([1, 1, 1, 2])   # 3 checkboxes + voice/quality options

with narration_cols[0]:
    narrate_breakfast = st.checkbox("🌅 Breakfast", value=False)
with narration_cols[1]:
    narrate_lunch     = st.checkbox("☀️ Lunch",     value=False)
with narration_cols[2]:
    narrate_dinner    = st.checkbox("🌙 Dinner",    value=False)

# Voice + quality options only appear when at least one meal is ticked
any_narration = narrate_breakfast or narrate_lunch or narrate_dinner
with narration_cols[3]:
    if any_narration:
        voice_col, quality_col = st.columns(2)
        with voice_col:
            tts_voice = st.selectbox("Voice",
                ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                index=0, label_visibility="visible")
        with quality_col:
            tts_quality = st.radio("Quality", ["tts-1", "tts-1-hd"],
                index=0, label_visibility="visible",
                help="tts-1 is faster; tts-1-hd sounds better.")
    else:
        tts_voice   = "alloy"
        tts_quality = "tts-1"

st.markdown("---")

# Build the list of meal keys selected for narration
narrate_keys = []
if narrate_breakfast: narrate_keys.append("breakfast")
if narrate_lunch:     narrate_keys.append("lunch")
if narrate_dinner:    narrate_keys.append("dinner")

generate_btn = st.button("✨ Generate Meal Plan", use_container_width=True)

# ---------------------------------------------------------------------------
# Generation — meal plan + TTS in one single wait
# ---------------------------------------------------------------------------

if generate_btn:
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("Please add your OpenAI API Key under Settings → Secrets.")
        st.stop()
    if not ingredients.strip():
        st.warning("Please enter at least one ingredient.")
        st.stop()

    with st.spinner("Crafting your meal plan…"):
        try:
            html_output, titles, meals = generate_meal_plan(
                ingredients=ingredients,
                kcal=kcal,
                exact_ingredients=exact_ingredients,
                extra=extra or None,
                diet=diet or None,
                model=model_choice,
                temperature=temperature,
            )
            st.session_state["html_output"] = html_output
            st.session_state["titles"]      = titles
            st.session_state["meals"]       = meals
            st.session_state["images"]      = {}
            st.session_state["narrations"]  = {}
        except Exception as exc:
            st.error(f"Error generating meal plan: {exc}")
            st.stop()

    # ── TTS runs immediately after, still inside the same "wait" ──────────
    if narrate_keys:
        meal_labels = {"breakfast": "🌅 Breakfast", "lunch": "☀️ Lunch", "dinner": "🌙 Dinner"}
        for key in narrate_keys:
            meal_data = st.session_state["meals"].get(key, {})
            script    = meal_data.get("narration", "")
            label     = meal_labels[key]
            if not script:
                st.warning(f"No narration script returned for {label}.")
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

# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------

if "html_output" in st.session_state:
    html_output = st.session_state["html_output"]
    titles      = st.session_state["titles"]
    meals       = st.session_state.get("meals", {})

    st.session_state.setdefault("images", {})
    st.session_state.setdefault("narrations", {})

    st.divider()
    st.markdown("## 🍽️ Your Meal Plan")

    if titles:
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in titles)
        st.markdown(tags_html, unsafe_allow_html=True)
        st.markdown("<br/>", unsafe_allow_html=True)

    with st.expander("📄 Full meal plan (rendered HTML)", expanded=True):
        st.components.v1.html(html_output, height=900, scrolling=True)

    st.download_button(label="⬇️ Download meal plan as HTML",
        data=html_output, file_name="daily_meal_plan.html", mime="text/html")

    # ---------------------------------------------------------------------------
    # Image generation
    # ---------------------------------------------------------------------------

    if generate_images and titles:
        st.divider()
        st.markdown("## 📸 Dish Images")
        if not os.environ.get("OPENAI_API_KEY"):
            st.warning("Add your API key in Streamlit Secrets to generate images.")
        else:
            img_cols = st.columns(len(titles))
            with tempfile.TemporaryDirectory() as tmpdir:
                for col, title in zip(img_cols, titles):
                    cached = st.session_state["images"].get(title)
                    if cached:
                        col.image(cached, caption=title, use_container_width=True)
                        continue
                    with col:
                        with st.spinner(f"Generating image for '{title}'…"):
                            try:
                                img_bytes = generate_meal_image(title=title, save_dir=tmpdir,
                                    extra="white background, food photography, top-down")
                                if img_bytes:
                                    st.session_state["images"][title] = img_bytes
                                    st.image(img_bytes, caption=title, use_container_width=True)
                                else:
                                    st.warning(f"No image returned for '{title}'.")
                            except Exception as exc:
                                st.error(f"Image error: {exc}")

    # ---------------------------------------------------------------------------
    # Audio narration results — shown only for meals that were generated
    # ---------------------------------------------------------------------------

    narrations = st.session_state["narrations"]
    if narrations:
        st.divider()
        st.markdown("## 🔊 Audio Narration")
        meal_labels = {"breakfast": "🌅 Breakfast", "lunch": "☀️ Lunch", "dinner": "🌙 Dinner"}

        for key, label in meal_labels.items():
            audio = narrations.get(key)
            if not audio:
                continue
            meal_title = meals.get(key, {}).get("title", label)
            st.markdown(f'<div class="narration-box"><strong>{label} — {meal_title}</strong></div>',
                unsafe_allow_html=True)
            st.audio(audio, format="audio/mp3")
            st.download_button(
                label=f"⬇️ Download {label} narration (MP3)",
                data=audio,
                file_name=f"{key}_narration.mp3",
                mime="audio/mp3",
                key=f"dl_{key}",
            )
            st.markdown("---")
