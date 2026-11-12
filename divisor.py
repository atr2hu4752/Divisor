import streamlit as st
import random
import re
import urllib.parse
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="Divisor Detective 🕵️‍♂️",
    page_icon="🧩",
    layout="centered"
)

# --- Default Spreadsheet Configuration ---
# Paste your full Google Sheet URL or ID here, or pass it via .streamlit/secrets.toml
DEFAULT_SHEET_URL = st.secrets.get(
    "GOOGLE_SHEET_URL", 
    "https://docs.google.com/spreadsheets/d/1OrTQ0UonsxQIWsid-GLcH-X8UcO4_Eu6ivlTUs7-wds/edit"
)

# --- Custom Kid-Friendly CSS & HTML Styles ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka+One&family=Quicksand:wght@500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Quicksand', sans-serif;
    }

    .title-box {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 24px;
        border-radius: 20px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    .title-box h1 {
        font-family: 'Fredoka One', cursive;
        margin: 0;
        font-size: 2.3rem;
        letter-spacing: 1px;
    }

    .puzzle-board {
        background-color: #f7faff;
        border: 3px dashed #4a90e2;
        border-radius: 24px;
        padding: 28px 16px;
        margin: 20px 0;
        display: flex;
        justify-content: center;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }

    .num-card {
        background: white;
        border-radius: 16px;
        padding: 12px 18px;
        min-width: 80px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.06);
        border: 2px solid #e2e8f0;
    }

    .num-card .label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #718096;
        margin-bottom: 4px;
    }

    .num-card .val {
        font-family: 'Fredoka One', cursive;
        font-size: 2rem;
        color: #2b6cb0;
    }

    .operator {
        font-family: 'Fredoka One', cursive;
        font-size: 2rem;
        color: #a0aec0;
        display: flex;
        align-items: center;
    }

    .unknown-card {
        background: #fffaf0;
        border: 3px solid #ed8936;
    }

    .unknown-card .val {
        color: #dd6b20;
    }

    .stat-badge {
        display: inline-block;
        background: #edf2f7;
        padding: 8px 16px;
        border-radius: 999px;
        font-weight: bold;
        color: #4a5568;
        margin: 0 4px;
    }

    .hint-box {
        background-color: #ebf8ff;
        border-left: 5px solid #3182ce;
        padding: 12px 18px;
        border-radius: 8px;
        margin-top: 15px;
        color: #2b6cb0;
        font-size: 0.95rem;
        line-height: 1.4;
    }

    /* Word Problem Card Styles */
    .word-problem-card {
        background: white;
        border: 2px solid #cbd5e1;
        border-radius: 20px;
        padding: 22px 20px;
        margin: 18px 0 20px 0;
        box-shadow: 0 6px 14px rgba(0,0,0,0.04);
    }

    .wp-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        flex-wrap: wrap;
        gap: 8px;
    }

    .wp-badge {
        background: #eff6ff;
        color: #1d4ed8;
        font-weight: 700;
        font-size: 0.85rem;
        padding: 4px 12px;
        border-radius: 999px;
        border: 1px solid #bfdbfe;
    }

    .wp-topic {
        background: #f1f5f9;
        color: #475569;
        font-weight: 700;
        font-size: 0.82rem;
        padding: 4px 10px;
        border-radius: 8px;
    }

    .problem-story {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1e293b;
        line-height: 1.55;
    }

    .explanation-box {
        background-color: #f0fdf4;
        border-left: 5px solid #22c55e;
        padding: 14px 18px;
        border-radius: 8px;
        margin-top: 14px;
        color: #15803d;
        font-size: 0.95rem;
        line-height: 1.45;
    }

    /* Responsive Option Buttons */
    div[data-testid="stColumn"] > div > div > button {
        font-family: 'Quicksand', 'Fredoka One', sans-serif !important;
        font-size: 1.12rem !important;
        font-weight: 700 !important;
        min-height: 64px !important;
        height: auto !important;
        padding: 10px 14px !important;
        white-space: normal !important;
        word-break: break-word !important;
        border-radius: 16px !important;
        border: 2px solid #cbd5e0 !important;
        background: white !important;
        color: #2d3748 !important;
        transition: all 0.15s ease-in-out !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }

    div[data-testid="stColumn"] > div > div > button:hover {
        border-color: #4a90e2 !important;
        color: #4a90e2 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(74,144,226,0.2) !important;
    }
</style>
""", unsafe_allow_html=True)


# --- Helper: Extract Sheet Key ---
def get_clean_sheet_id(url_or_id: str) -> str:
    url_or_id = url_or_id.strip()
    if "/d/" in url_or_id:
        return url_or_id.split("/d/")[1].split("/")[0]
    return url_or_id


# --- Live Google Sheets Loader using Pandas ---
@st.cache_data(ttl=60)
def load_live_division_questions(sheet_url_or_id: str, tab_name: str = "Division"):
    """
    Directly queries Google Sheets GViz endpoint with Pandas to read the live questions.
    Caches data for 60 seconds so student clicks remain fast.
    """
    clean_id = get_clean_sheet_id(sheet_url_or_id)
    if not clean_id or "YOUR_SPREADSHEET_ID" in clean_id:
        return None, "Please provide a valid Google Sheet URL or ID in the sidebar."

    encoded_tab = urllib.parse.quote(tab_name)
    gviz_url = f"https://docs.google.com/spreadsheets/d/{clean_id}/gviz/tq?tqx=out:csv&sheet={encoded_tab}"

    try:
        df = pd.read_csv(gviz_url)
        # Normalize column names to lowercase without spaces
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        required_cols = {"question", "option_a", "option_b", "option_c", "option_d", "correct"}
        if not required_cols.issubset(set(df.columns)):
            missing = required_cols - set(df.columns)
            return None, f"Missing required columns in tab '{tab_name}': {missing}"

        records = []
        for idx, row in df.iterrows():
            # Skip empty rows
            if pd.isna(row.get("question")):
                continue

            records.append({
                "id": int(row.get("id", idx + 1)) if pd.notna(row.get("id")) else (idx + 1),
                "title": str(row.get("title", "Division Problem")),
                "question": str(row.get("question", "")),
                "option_a": str(row.get("option_a", "")),
                "option_b": str(row.get("option_b", "")),
                "option_c": str(row.get("option_c", "")),
                "option_d": str(row.get("option_d", "")),
                "correct": str(row.get("correct", "a")).strip().lower(),
                "explanation": str(row.get("explanation", "Great job!")) if pd.notna(row.get("explanation")) else ""
            })

        if not records:
            return None, f"Tab '{tab_name}' was reached but no question rows were found."

        return records, None

    except Exception as e:
        return None, f"Could not read from Google Sheets: {e}. Check that the spreadsheet is shared as 'Anyone with the link can view'."


# --- Helper: Equation Generator for Number Modes ---
def generate_problem(max_dividend):
    max_d = min(12, max(2, max_dividend // 2))
    divisor = random.randint(2, max_d)
    max_q = max(1, (max_dividend - (divisor - 1)) // divisor)
    quotient = random.randint(1, max_q)
    remainder = random.randint(0, divisor - 1)
    dividend = (divisor * quotient) + remainder

    min_possible_divisor = remainder + 1
    distractors = set()

    offsets = [-3, -2, -1, 1, 2, 3]
    random.shuffle(offsets)
    for offset in offsets:
        candidate = divisor + offset
        if candidate >= min_possible_divisor and candidate != divisor:
            distractors.add(candidate)
        if len(distractors) == 3:
            break

    while len(distractors) < 3:
        candidate = random.randint(max(2, min_possible_divisor), max(divisor + 6, min_possible_divisor + 6))
        if candidate != divisor:
            distractors.add(candidate)

    options = sorted(list(distractors) + [divisor])

    return {
        "dividend": dividend,
        "quotient": quotient,
        "remainder": remainder,
        "divisor": divisor,
        "options": options
    }


# --- Session State Initialization ---
if "score" not in st.session_state:
    st.session_state.score = 0
if "streak" not in st.session_state:
    st.session_state.streak = 0
if "show_hint" not in st.session_state:
    st.session_state.show_hint = False
if "feedback" not in st.session_state:
    st.session_state.feedback = None
if "selected_answer" not in st.session_state:
    st.session_state.selected_answer = None
if "problem" not in st.session_state:
    st.session_state.problem = generate_problem(50)
if "wp_index" not in st.session_state:
    st.session_state.wp_index = 0
if "sheet_url" not in st.session_state:
    st.session_state.sheet_url = DEFAULT_SHEET_URL


# --- Sidebar Configurations ---
with st.sidebar:
    st.header("⚙️ Game Settings")
    
    game_mode = st.radio(
        "🎮 Answer Mode:",
        options=[
            "Multiple Choice (Buttons)",
            "Type Your Answer",
            "Multiple Choice (Word Problems)"
        ],
        index=0
    )

    # Detect mode switch to reset temporary card states
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = game_mode
    elif st.session_state.current_mode != game_mode:
        st.session_state.current_mode = game_mode
        st.session_state.feedback = None
        st.session_state.selected_answer = None
        st.session_state.show_hint = False

    if game_mode in ["Multiple Choice (Buttons)", "Type Your Answer"]:
        max_num = st.slider(
            "Maximum Dividend (Number)",
            min_value=20,
            max_value=100,
            value=50,
            step=10,
            help="Controls the largest possible dividend in equation mode."
        )
    else:
        max_num = 100
        st.markdown("---")
        st.subheader("🔗 Live Google Sheets Link")
        sheet_input = st.text_input(
            "Spreadsheet Link / ID:",
            value=st.session_state.sheet_url,
            help="Direct link to your Google Sheet with tab 'Division'."
        )
        if sheet_input != st.session_state.sheet_url:
            st.session_state.sheet_url = sheet_input

        col_ref1, col_ref2 = st.columns([1, 1])
        with col_ref1:
            if st.button("🔄 Sync Live Sheet"):
                st.cache_data.clear()
                st.session_state.feedback = None
                st.session_state.selected_answer = None
                st.session_state.show_hint = False
                st.rerun()
        with col_ref2:
            if st.button("🔀 Shuffle Order"):
                st.session_state.feedback = None
                st.session_state.selected_answer = None
                st.session_state.show_hint = False
                st.session_state.wp_index = random.randint(0, 19)
                st.rerun()

    if st.button("🔄 Reset Score"):
        st.session_state.score = 0
        st.session_state.streak = 0
        st.session_state.feedback = None
        st.session_state.show_hint = False
        st.session_state.selected_answer = None
        st.session_state.problem = generate_problem(max_num)
        st.session_state.wp_index = 0
        st.rerun()

    st.markdown("---")
    st.markdown("**Rule Reminder:**")
    st.latex(r"\text{Dividend} = (\text{Divisor} \times \text{Quotient}) + \text{Remainder}")
    st.caption("Remember: The Divisor is always bigger than the Remainder!")


# --- Header & Stats Bar ---
st.markdown("""
<div class="title-box">
    <h1>🕵️ Divisor Detective</h1>
    <p>Find the missing divisor to crack the code!</p>
</div>
""", unsafe_allow_html=True)

col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.markdown(f"<div class='stat-badge'>⭐ Points: <b>{st.session_state.score}</b></div>", unsafe_allow_html=True)
with col_s2:
    st.markdown(f"<div class='stat-badge'>🔥 Streak: <b>{st.session_state.streak}</b></div>", unsafe_allow_html=True)
with col_s3:
    if game_mode == "Multiple Choice (Word Problems)":
        st.markdown("<div class='stat-badge'>📚 Mode: <b>Live Sheet</b></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='stat-badge'>🎯 Max Limit: <b>{max_num}</b></div>", unsafe_allow_html=True)


# ==============================================================================
# MODE 1 & 2: EQUATION PUZZLE BOARDS
# ==============================================================================
if game_mode in ["Multiple Choice (Buttons)", "Type Your Answer"]:
    p = st.session_state.problem

    html_card = f"""
    <div class="puzzle-board">
        <div class="num-card">
            <div class="label">Total Number</div>
            <div class="val">{p['dividend']}</div>
        </div>
        <div class="operator">÷</div>
        <div class="num-card unknown-card">
            <div class="label">Divisor</div>
            <div class="val">?</div>
        </div>
        <div class="operator">=</div>
        <div class="num-card">
            <div class="label">Quotient</div>
            <div class="val">{p['quotient']}</div>
        </div>
        <div class="operator">+</div>
        <div class="num-card">
            <div class="label">Remainder</div>
            <div class="val">{p['remainder']}</div>
        </div>
    </div>
    """
    st.markdown(html_card, unsafe_allow_html=True)

    def check_choice(choice):
        st.session_state.selected_answer = choice
        if choice == p["divisor"]:
            st.session_state.score += 10
            st.session_state.streak += 1
            st.session_state.feedback = "correct"
            st.balloons()
        else:
            st.session_state.streak = 0
            st.session_state.feedback = "incorrect"

    if game_mode == "Multiple Choice (Buttons)":
        st.markdown("<p style='text-align: center; font-weight: bold; color: #4a5568;'>Tap the correct divisor:</p>", unsafe_allow_html=True)
        btn_row1 = st.columns(2)
        btn_row2 = st.columns(2)
        all_btn_cols = [btn_row1[0], btn_row1[1], btn_row2[0], btn_row2[1]]

        for i, opt in enumerate(p["options"]):
            with all_btn_cols[i]:
                is_disabled = st.session_state.feedback == "correct"
                if st.button(f"{opt}", key=f"choice_btn_{i}", disabled=is_disabled, use_container_width=True):
                    check_choice(opt)
    else:
        with st.form(key="answer_form", clear_on_submit=True):
            col_input, col_btn = st.columns([2, 1])
            with col_input:
                user_guess = st.number_input(
                    "Enter the missing Divisor:",
                    min_value=1,
                    max_value=max_num,
                    step=1,
                    value=None,
                    placeholder="Type your number..."
                )
            with col_btn:
                st.write("")
                st.write("")
                submit = st.form_submit_button("Check Answer! 🚀", use_container_width=True)

        if submit:
            if user_guess is None:
                st.warning("Please enter a number first!")
            else:
                check_choice(user_guess)

    if st.session_state.feedback == "correct":
        st.success(f"🎉 **Awesome!** {p['dividend']} ÷ **{p['divisor']}** = {p['quotient']} with remainder {p['remainder']}.")
        if st.button("Next Challenge ➡️", use_container_width=True):
            st.session_state.problem = generate_problem(max_num)
            st.session_state.feedback = None
            st.session_state.selected_answer = None
            st.session_state.show_hint = False
            st.rerun()

    elif st.session_state.feedback == "incorrect":
        st.error(f"❌ **{st.session_state.selected_answer}** is not right! Try another button, or click **Need a Hint?** below.")

    col_hint, _ = st.columns([1, 1])
    with col_hint:
        if st.button("💡 Need a Hint?"):
            st.session_state.show_hint = not st.session_state.show_hint

    if st.session_state.show_hint:
        diff = p['dividend'] - p['remainder']
        st.markdown(f"""
        <div class="hint-box">
            <b>Step 1:</b> Subtract the remainder from the total:<br>
            <code>{p['dividend']} - {p['remainder']} = {diff}</code><br><br>
            <b>Step 2:</b> Divide that result by the quotient ({p['quotient']}):<br>
            <code>{diff} ÷ {p['quotient']} = ?</code>
        </div>
        """, unsafe_allow_html=True)


# ==============================================================================
# MODE 3: LIVE LINKED WORD PROBLEMS (TAB: "Division")
# ==============================================================================
else:
    questions, err_msg = load_live_division_questions(st.session_state.sheet_url, tab_name="Division")

    if err_msg or not questions:
        st.error(f"⚠️ {err_msg}")
        st.info("💡 **Quick Setup Checklist:**\n1. In your Google Sheet, click **Share** -> Change to **Anyone with the link can view**.\n2. Paste your Google Sheet URL into the sidebar input field.")
    else:
        current_wp = questions[st.session_state.wp_index % len(questions)]

        # Word Problem Mission Card
        wp_card_html = f"""
        <div class="word-problem-card">
            <div class="wp-header">
                <span class="wp-badge">Case File #{current_wp['id']:02d}</span>
                <span class="wp-topic">🏷️ {current_wp['title']}</span>
            </div>
            <div class="problem-story">
                {current_wp['question']}
            </div>
        </div>
        """
        st.markdown(wp_card_html, unsafe_allow_html=True)

        def check_word_problem(choice_letter):
            st.session_state.selected_answer = choice_letter
            if choice_letter == current_wp["correct"]:
                st.session_state.score += 10
                st.session_state.streak += 1
                st.session_state.feedback = "correct"
                st.balloons()
            else:
                st.session_state.streak = 0
                st.session_state.feedback = "incorrect"

        st.markdown("<p style='text-align: center; font-weight: bold; color: #4a5568;'>Select the best answer:</p>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        col_c, col_d = st.columns(2)
        is_disabled = st.session_state.feedback == "correct"

        with col_a:
            if st.button(f"A. {current_wp['option_a']}", key="btn_wp_a", disabled=is_disabled, use_container_width=True):
                check_word_problem("a")
        with col_b:
            if st.button(f"B. {current_wp['option_b']}", key="btn_wp_b", disabled=is_disabled, use_container_width=True):
                check_word_problem("b")
        with col_c:
            if st.button(f"C. {current_wp['option_c']}", key="btn_wp_c", disabled=is_disabled, use_container_width=True):
                check_word_problem("c")
        with col_d:
            if st.button(f"D. {current_wp['option_d']}", key="btn_wp_d", disabled=is_disabled, use_container_width=True):
                check_word_problem("d")

        if st.session_state.feedback == "correct":
            correct_key = current_wp["correct"]
            correct_val = current_wp.get(f"option_{correct_key}", "")
            st.success(f"🎉 **Brilliant Detective Work!** Option **{correct_key.upper()} ({correct_val})** is correct!")
            
            if current_wp.get("explanation"):
                st.markdown(f"""
                <div class="explanation-box">
                    <b>💡 Step-by-Step Solution:</b><br>
                    {current_wp['explanation']}
                </div>
                """, unsafe_allow_html=True)

            if st.button("Next Case File ➡️", use_container_width=True):
                st.session_state.wp_index = (st.session_state.wp_index + 1) % len(questions)
                st.session_state.feedback = None
                st.session_state.selected_answer = None
                st.session_state.show_hint = False
                st.rerun()

        elif st.session_state.feedback == "incorrect":
            chosen_key = st.session_state.selected_answer
            chosen_val = current_wp.get(f"option_{chosen_key}", "")
            st.error(f"❌ Option **{chosen_key.upper()} ({chosen_val})** is not right! Try another option or click **Need a Hint?** below.")

        col_hint, _ = st.columns([1, 1])
        with col_hint:
            if st.button("💡 Need a Hint?"):
                st.session_state.show_hint = not st.session_state.show_hint

        if st.session_state.show_hint:
            explanation_text = current_wp.get("explanation", "")
            first_step = explanation_text.split(".")[0] + "." if explanation_text else "Subtract the remainder from the dividend first."
            st.markdown(f"""
            <div class="hint-box">
                <b>Detective Clue:</b> {first_step}<br>
                <em>Case Objective: {current_wp['title']}</em>
            </div>
            """, unsafe_allow_html=True)
