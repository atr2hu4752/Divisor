import streamlit as st
import random

# --- Page Configuration ---
st.set_page_config(
    page_title="Divisor Detective 🕵️‍♂️",
    page_icon="🧩",
    layout="centered"
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
    }

    /* Large, colorful multiple-choice buttons */
    div[data-testid="stColumn"] > div > div > button {
        font-family: 'Fredoka One', cursive !important;
        font-size: 1.8rem !important;
        height: 70px !important;
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


# --- Helper: Problem & Options Generator ---
def generate_problem(max_dividend):
    """
    Generates a division problem:
    Dividend = Divisor * Quotient + Remainder, with 0 <= Remainder < Divisor.
    Also produces 4 distinct multiple-choice options (1 correct, 3 plausible distractors).
    """
    max_d = min(12, max(2, max_dividend // 2))
    divisor = random.randint(2, max_d)

    max_q = max(1, (max_dividend - (divisor - 1)) // divisor)
    quotient = random.randint(1, max_q)

    remainder = random.randint(0, divisor - 1)
    dividend = (divisor * quotient) + remainder

    # Generate 3 plausible distractors that must be > remainder (since Divisor > Remainder)
    min_possible_divisor = remainder + 1
    distractors = set()

    # Step 1: Try adjacent numbers first (e.g., divisor +/- 1, 2, 3)
    offsets = [-3, -2, -1, 1, 2, 3]
    random.shuffle(offsets)
    for offset in offsets:
        candidate = divisor + offset
        if candidate >= min_possible_divisor and candidate != divisor:
            distractors.add(candidate)
        if len(distractors) == 3:
            break

    # Step 2: Fallback to random numbers if adjacent pool was too small
    while len(distractors) < 3:
        candidate = random.randint(max(2, min_possible_divisor), max(divisor + 6, min_possible_divisor + 6))
        if candidate != divisor:
            distractors.add(candidate)

    options = list(distractors) + [divisor]
    random.shuffle(options)

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


# --- Sidebar Configurations ---
with st.sidebar:
    st.header("⚙️ Game Settings")
    
    game_mode = st.radio(
        "🎮 Answer Mode:",
        options=["Multiple Choice (Buttons)", "Type Your Answer"],
        index=0
    )

    max_num = st.slider(
        "Maximum Dividend (Number)",
        min_value=20,
        max_value=100,
        value=50,
        step=10,
        help="Controls the largest possible dividend in the game."
    )

    if st.button("🔄 Reset Score"):
        st.session_state.score = 0
        st.session_state.streak = 0
        st.session_state.feedback = None
        st.session_state.show_hint = False
        st.session_state.selected_answer = None
        st.session_state.problem = generate_problem(max_num)
        st.rerun()

    st.markdown("---")
    st.markdown("**Rule Reminder:**")
    st.latex(r"\text{Dividend} = (\text{Divisor} \times \text{Quotient}) + \text{Remainder}")
    st.caption("Remember: The Divisor is always bigger than the Remainder!")


# --- Header & Stats Bar ---
st.markdown("""
<div class="title-box">
    <h1>🕵️ Divisor Detective for Alice</h1>
    <p>Find the missing divisor to crack the code!</p>
</div>
""", unsafe_allow_html=True)

col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.markdown(f"<div class='stat-badge'>⭐ Points: <b>{st.session_state.score}</b></div>", unsafe_allow_html=True)
with col_s2:
    st.markdown(f"<div class='stat-badge'>🔥 Streak: <b>{st.session_state.streak}</b></div>", unsafe_allow_html=True)
with col_s3:
    st.markdown(f"<div class='stat-badge'>🎯 Max Limit: <b>{max_num}</b></div>", unsafe_allow_html=True)


# --- Render Puzzle Board in HTML ---
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


# --- Answer Checking Function ---
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


# --- Input Area (Multiple Choice or Typing) ---
if game_mode == "Multiple Choice (Buttons)":
    st.markdown("<p style='text-align: center; font-weight: bold; color: #4a5568;'>Tap the correct divisor:</p>", unsafe_allow_html=True)
    
    # 2x2 grid for responsive kid-friendly tap targets
    btn_row1 = st.columns(2)
    btn_row2 = st.columns(2)
    all_btn_cols = [btn_row1[0], btn_row1[1], btn_row2[0], btn_row2[1]]

    for i, opt in enumerate(p["options"]):
        with all_btn_cols[i]:
            # Disable buttons once solved correctly until Next Challenge is clicked
            is_disabled = st.session_state.feedback == "correct"
            if st.button(f"{opt}", key=f"choice_btn_{i}", disabled=is_disabled, use_container_width=True):
                check_choice(opt)

else:
    # Manual typing mode fallback
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


# --- Feedback & Actions ---
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


# --- Interactive Hint System ---
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
