"""
app.py — Streamlit UI for the Daily Meal Planner.
All display / interaction code lives here.
Business logic is imported from meal_logic.py.
"""

import os
import tempfile
import streamlit as st

from meal_logic import generate_meal_plan, generate_meal_image

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Daily Meal Planner",
    page_icon="🥗",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .main-title {
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        font-weight: 700;
        color: #1a3c2e;
        letter-spacing: -0.02em;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 1.05rem;
        color: #5a7a6a;
        font-weight: 300;
        margin-top: 0.25rem;
        margin-bottom: 2rem;
    }

    .section-label {
        font-size: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #6b8f7e;
        margin-bottom: 0.4rem;
    }

    .meal-card {
        background: #f7faf8;
        border-left: 4px solid #3d8b5e;
        border-radius: 0 8px 8px 0;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }

    .image-caption {
        font-size: 0.8rem;
        color: #6b8f7e;
        text-align: center;
        margin-top: 0.5rem;
        font-style: italic;
    }

    .stButton > button {
        background-color: #1a3c2e;
        color: #f0f7f4;
        border: none;
        border-radius: 6px;
        padding: 0.6rem 1.8rem;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        font-size: 0.95rem;
        letter-spacing: 0.03em;
        transition: background 0.2s;
        width: 100%;
    }

    .stButton > button:hover {
        background-color: #2d6b4a;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        border-radius: 6px;
        border: 1.5px solid #d0e4da;
        font-family: 'DM Sans', sans-serif;
    }

    div[data-testid="stExpander"] {
        border: 1.5px solid #d0e4da;
        border-radius: 8px;
    }

    .tag {
        display: inline-block;
        background: #dff0e8;
        color: #1a3c2e;
        border-radius: 20px;
        padding: 0.2rem 0.75rem;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
# Sidebar — settings
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ⚙️ Settings")

    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

    api_key = st.text_input(
        "OpenAI API Key (leave blank if set in secrets)",
        type="password",
        placeholder="sk-...",
        help="Your key is used only for this session and never stored.",
    )
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    st.markdown("---")

    kcal = st.number_input(
        "Daily calorie target (kcal)",
        min_value=800,
        max_value=5000,
        value=2000,
        step=50,
    )

    exact_ingredients = st.toggle(
        "Use ONLY listed ingredients",
        value=False,
        help="When on, the AI will not add any extra ingredients.",
    )

    model_choice = st.selectbox(
        "Chat model",
        ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        index=2,
    )

    temperature = st.slider(
        "Creativity (temperature)",
        min_value=0.0,
        max_value=2.0,
        value=1.0,
        step=0.1,
    )

    generate_images = st.toggle(
        "Generate dish images (DALL-E 3)",
        value=False,
        help="Generates one image per meal. Increases cost and time.",
    )

    st.markdown("---")
    st.markdown(
        "<small>Converted from a Jupyter notebook. "
        "Business logic lives in <code>meal_logic.py</code>.</small>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main form
# ---------------------------------------------------------------------------

col_left, col_right = st.columns([2, 1], gap="large")

with col_left:
    st.markdown('<p class="section-label">Base Ingredients</p>', unsafe_allow_html=True)
    ingredients = st.text_area(
        label="Ingredients",
        label_visibility="collapsed",
        value=(
            "extra-virgin olive oil, whole grains, fresh fruits and vegetables, "
            "nuts and seeds, fish, eggs, fermented foods, honey"
        ),
        height=110,
        placeholder="e.g. chicken, broccoli, quinoa, lemon, garlic …",
    )

with col_right:
    st.markdown('<p class="section-label">Extra Dietary Notes (optional)</p>', unsafe_allow_html=True)
    extra = st.text_input(
        label="Extra notes",
        label_visibility="collapsed",
        placeholder="e.g. spicy, low-carb, vegan …",
    )
    st.markdown("<br/>", unsafe_allow_html=True)
    generate_btn = st.button("✨ Generate Meal Plan", use_container_width=True)

# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

if generate_btn:
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("Please enter your OpenAI API Key in the sidebar first.")
        st.stop()

    if not ingredients.strip():
        st.warning("Please enter at least one ingredient.")
        st.stop()

    with st.spinner("Crafting your meal plan…"):
        try:
            html_output, titles = generate_meal_plan(
                ingredients=ingredients,
                kcal=kcal,
                exact_ingredients=exact_ingredients,
                extra=extra or None,
                model=model_choice,
                temperature=temperature,
            )
            st.session_state["html_output"] = html_output
            st.session_state["titles"] = titles
            st.session_state["images"] = {}   # reset images from prior run
        except Exception as exc:
            st.error(f"Error generating meal plan: {exc}")
            st.stop()

# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------

if "html_output" in st.session_state:
    html_output: str = st.session_state["html_output"]
    titles: list[str] = st.session_state["titles"]

    st.divider()
    st.markdown("## 🍽️ Your Meal Plan")

    # Show detected titles as tags
    if titles:
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in titles)
        st.markdown(tags_html, unsafe_allow_html=True)
        st.markdown("<br/>", unsafe_allow_html=True)

    # Render the HTML meal plan inside an expandable section
    with st.expander("📄 Full meal plan (rendered HTML)", expanded=True):
        st.components.v1.html(html_output, height=900, scrolling=True)

    # Raw HTML download
    st.download_button(
        label="⬇️ Download meal plan as HTML",
        data=html_output,
        file_name="daily_meal_plan.html",
        mime="text/html",
    )

    # ---------------------------------------------------------------------------
    # Image generation (optional)
    # ---------------------------------------------------------------------------

    if generate_images and titles:
        st.divider()
        st.markdown("## 📸 Dish Images")

        if not os.environ.get("OPENAI_API_KEY"):
            st.warning("Add your API key in the sidebar to generate images.")
        else:
            img_cols = st.columns(len(titles))
            with tempfile.TemporaryDirectory() as tmpdir:
                for idx, (col, title) in enumerate(zip(img_cols, titles)):
                    # Use cached image if already generated this session
                    cached = st.session_state["images"].get(title)
                    if cached:
                        col.image(cached, caption=title, use_container_width=True)
                        continue

                    with col:
                        with st.spinner(f"Generating image for '{title}'…"):
                            try:
                                img_path = generate_meal_image(
                                    title=title,
                                    save_dir=tmpdir,
                                    extra="white background, food photography, top-down",
                                )
                                if img_path:
                                    # Read bytes so they survive tmpdir cleanup
                                    with open(img_path, "rb") as f:
                                        img_bytes = f.read()
                                    st.session_state["images"][title] = img_bytes
                                    st.image(img_bytes, caption=title, use_container_width=True)
                                else:
                                    st.warning("Image generation failed.")
                            except Exception as exc:
                                st.error(f"Image error: {exc}")
