import streamlit as st
import json
import os
import random
from collections import deque

st.set_page_config(page_title="Cert Flashcards", page_icon="🧠", layout="centered")

# --- Custom CSS for better aesthetics ---
st.markdown("""
<style>
    /* Premium aesthetics */
    .main {
        background-color: #f8f9fa;
    }
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
    }
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s ease;
        font-weight: 500;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
        border: 1px solid #f0f0f0;
    }
    .footer {
        text-align: center;
        color: #888;
        font-size: 0.9rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧠 Cert Flashcards")
st.markdown("Practice cloud certification exam questions with interactive flashcards.")

# ------------------------------------------------
# Load questions
# ------------------------------------------------
DATA_DIR = "data"

@st.cache_data
def load_questions(data_dir=DATA_DIR):
    """Load all .json question files."""
    questions = []
    if not os.path.exists(data_dir):
        return questions
        
    for file in os.listdir(data_dir):
        if file.endswith(".json"):
            try:
                with open(os.path.join(data_dir, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        questions.extend(data)
            except Exception as e:
                st.sidebar.error(f"Error loading {file}: {e}")
    return questions

questions = load_questions()
if not questions:
    st.error("⚠️ No JSON files found in `data/` folder. Please add some question files.")
    st.stop()

# ------------------------------------------------
# Sidebar settings
# ------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    # Optional random seed for reproducibility
    seed_value = st.text_input(
        "Random seed (leave blank for random order):",
        value="",
        help="Enter a number or text — same seed gives same order each time."
    )
    if seed_value.strip():
        try:
            random.seed(int(seed_value))
        except ValueError:
            random.seed(seed_value.strip())
    else:
        random.seed()  # randomize every run

    # Collect all unique sections
    sections = sorted(list({q.get("section_name", "Unknown Section") for q in questions if q.get("section_name")}))
    if not sections:
        sections = ["All"]
        
    # Safe default for multiselect
    default_section = [sections[0]] if sections else []
    
    selected_sections = st.multiselect(
        "📘 Filter by section:",
        options=sections,
        default=default_section,
    )

filtered_questions = [q for q in questions if q.get("section_name", "Unknown Section") in selected_sections or "All" in selected_sections]
if not filtered_questions:
    st.warning("No questions found for the selected section(s).")
    st.stop()

# Shuffle & maintain state so it doesn't reshuffle on every button click
if "filtered_questions" not in st.session_state or st.session_state.get("seed_value") != seed_value or st.session_state.get("selected_sections") != selected_sections:
    shuffled_qs = list(filtered_questions)
    random.shuffle(shuffled_qs)
    st.session_state.filtered_questions = shuffled_qs
    st.session_state.seed_value = seed_value
    st.session_state.selected_sections = selected_sections
    st.session_state.current_index = 1
    st.session_state.results = []
    st.session_state.recent_results = deque(maxlen=10)

# Use the stateful questions list
active_questions = st.session_state.filtered_questions
total = len(active_questions)

# ------------------------------------------------
# Jump to question
# ------------------------------------------------
with st.sidebar.expander("🔢 Jump to question"):
    jump_index = st.number_input(
        "Enter question number:",
        min_value=1,
        max_value=total,
        value=st.session_state.current_index,
        step=1
    )
    if st.button("Go", use_container_width=True):
        st.session_state.current_index = jump_index
        st.rerun()

# ------------------------------------------------
# Stats display
# ------------------------------------------------
if st.session_state.results:
    total_attempts = len(st.session_state.results)
    total_correct = sum(st.session_state.results)
    overall_accuracy = (total_correct / total_attempts) * 100

    recent_correct = sum(st.session_state.recent_results)
    recent_accuracy = (recent_correct / len(st.session_state.recent_results)) * 100

    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Performance")
    colA, colB = st.sidebar.columns(2)
    colA.metric("Overall", f"{overall_accuracy:.1f}%")
    colB.metric("Last 10", f"{recent_accuracy:.1f}%")

# ------------------------------------------------
# Display flashcard
# ------------------------------------------------
index = st.session_state.current_index
question = active_questions[index - 1]
prompt = question.get("prompt", "")
answers = question.get("answers", [])

# Ensure answers are shuffled securely per question
if f"shuffled_answers_{index}" not in st.session_state:
    ans_copy = list(answers)
    random.shuffle(ans_copy)
    st.session_state[f"shuffled_answers_{index}"] = ans_copy

display_answers = st.session_state[f"shuffled_answers_{index}"]

# Progress Bar
progress = index / total
st.progress(progress, text=f"Question {index} of {total}")

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(f"### {prompt}")
st.markdown("<br>", unsafe_allow_html=True)

if not display_answers:
    st.info("This question has no multiple choice options.")
else:
    correct_answers = [a for a in display_answers if a.get("isCorrect")]
    num_correct = len(correct_answers)
    
    selected_options = []
    if num_correct > 1:
        st.write(f"**Select {num_correct} answers:**")
        for a in display_answers:
            if st.checkbox(a["text"], key=f"check_{index}_{a['text']}"):
                selected_options.append(a["text"])
    else:
        selected = st.radio(
            "**Select your answer:**",
            [a["text"] for a in display_answers],
            key=f"answer_{index}",
            index=None
        )
        if selected is not None:
            selected_options.append(selected)

    if st.button("Check Answer", type="primary", key=f"check_{index}"):
        if not selected_options:
            st.warning("Please select an answer first.")
        else:
            if not correct_answers:
                st.warning("This question does not have a designated correct answer in the dataset.")
            else:
                correct_texts = [a["text"] for a in correct_answers]
                
                if num_correct > 1:
                    is_correct = set(selected_options) == set(correct_texts)
                else:
                    is_correct = selected_options[0] in correct_texts

                # Store results
                st.session_state.results.append(is_correct)
                st.session_state.recent_results.append(is_correct)

                # Feedback
                if is_correct:
                    st.success("✅ Correct!")
                    for c_ans in correct_answers:
                        if c_ans.get("explanation"):
                            st.info(f"**Explanation:** {c_ans['explanation']}")
                else:
                    st.error("❌ Incorrect!")
                    for s in selected_options:
                        if s not in correct_texts:
                            chosen_obj = next((a for a in display_answers if a["text"] == s), None)
                            if chosen_obj and chosen_obj.get("explanation"):
                                st.warning(f"**Why '{s}' is wrong:** {chosen_obj['explanation']}")
                    
                    st.info(f"**Correct answer(s):** {', '.join(correct_texts)}")
                    for c_ans in correct_answers:
                        if c_ans.get("explanation"):
                            st.caption(f"*Explanation for {c_ans['text']}:* {c_ans['explanation']}")

st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------
# Metadata + navigation
# ------------------------------------------------
with st.expander("📚 View Question Metadata"):
    st.write(f"**ID:** `{question.get('question_id', 'N/A')}`")
    st.write(f"**Section:** `{question.get('section_name', 'N/A')}`")
    st.write(f"**Bloom Level:** `{question.get('bloom_level', 'N/A')}`")
    if 'question_choice_type' in question:
        st.write(f"**Choice Type:** `{question.get('question_choice_type')}`")
    tags = question.get('tags', [])
    if tags:
        st.write(f"**Tags:** {', '.join(tags)}")
    if question.get('idea_text'):
        st.write(f"**Idea Text:** {question.get('idea_text')}")

st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("⬅ Previous", use_container_width=True, disabled=(index == 1)):
        st.session_state.current_index -= 1
        st.rerun()

with col3:
    if st.button("Next ➡", use_container_width=True, disabled=(index == total)):
        st.session_state.current_index += 1
        st.rerun()

st.markdown(
    """
    <div class="footer">
        © 2025 Mishal Faisal | Built with ❤️ using Streamlit
    </div>
    """,
    unsafe_allow_html=True
)

