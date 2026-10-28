import json
import random
from collections import deque
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Cert Flashcards", page_icon="🧠", layout="centered")

DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_questions():
    """Load every question from data/*.json."""
    questions = []
    for path in sorted(DATA_DIR.glob("*.json")):
        try:
            questions.extend(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as e:
            st.sidebar.error(f"Error loading {path.name}: {e}")
    return questions


def md(text):
    """Render plain question text as Markdown: keep line breaks, don't treat `$` as LaTeX."""
    return text.replace("$", "\\$").replace("\n", "  \n")


questions = load_questions()
if not questions:
    st.error("No question files found in `data/`.")
    st.stop()

# ------------------------------------------------
# Sidebar: exam, order, navigation, stats
# ------------------------------------------------
with st.sidebar:
    st.title("🧠 Cert Flashcards")
    sections = sorted({q["section_name"] for q in questions})
    selected_sections = st.multiselect("Exam", sections, default=sections[:1], placeholder="Choose an exam")
    seed = st.text_input("Shuffle seed", help="The same seed gives the same question order. Leave blank for random.").strip()

if not selected_sections:
    st.info("👈 Choose an exam in the sidebar to start.")
    st.stop()

# Reshuffle only when the exam selection or seed changes, not on every click
state_key = (seed, tuple(selected_sections))
if st.session_state.get("state_key") != state_key:
    order = [q for q in questions if q["section_name"] in selected_sections]
    random.Random(seed or None).shuffle(order)
    st.session_state.update(state_key=state_key, order=order, index=0, attempts={}, recent=deque(maxlen=10))

order = st.session_state.order
attempts = st.session_state.attempts
total = len(order)
i = st.session_state.index

with st.sidebar:
    jump = st.number_input("Go to question", min_value=1, max_value=total, value=i + 1, step=1)
    if st.button("Go", width="stretch"):
        st.session_state.index = jump - 1
        st.rerun()

    if attempts:
        st.divider()
        st.subheader("📊 Performance")
        recent = st.session_state.recent
        c1, c2 = st.columns(2)
        c1.metric("Overall", f"{sum(a['correct'] for a in attempts.values()) / len(attempts):.0%}")
        c2.metric("Last 10", f"{sum(recent) / len(recent):.0%}")
        st.caption(f"{len(attempts)} of {total} answered")

# ------------------------------------------------
# Flashcard
# ------------------------------------------------
q = order[i]
qid = q["question_id"]
correct_texts = {a["text"] for a in q["answers"] if a["isCorrect"]}
multi = len(correct_texts) > 1

key = f"shuffled-{qid}"
if key not in st.session_state:
    st.session_state[key] = random.Random(f"{seed}-{qid}" if seed else None).sample(q["answers"], len(q["answers"]))
answers = st.session_state[key]
attempt = attempts.get(qid)

st.progress((i + 1) / total, text=f"Question {i + 1} of {total}")

with st.container(border=True):
    st.caption(f"{q['section_name']} · {qid}")
    if multi:
        st.badge(f"Select {len(correct_texts)}", icon=":material/checklist:", color="violet")
    st.markdown(md(q["prompt"]))
    st.write("")

    if attempt is None:
        if multi:
            selected = [a["text"] for a in answers if st.checkbox(md(a["text"]), key=f"cb-{qid}-{a['text']}")]
        else:
            choice = st.radio("Your answer", [a["text"] for a in answers], index=None, format_func=md,
                              key=f"radio-{qid}", label_visibility="collapsed")
            selected = [choice] if choice else []

        if st.button("Check answer", type="primary", icon=":material/check:", disabled=not selected, key=f"check-{qid}"):
            ok = set(selected) == correct_texts
            attempts[qid] = {"selected": selected, "correct": ok}
            st.session_state.recent.append(ok)
            st.rerun()
    else:
        if attempt["correct"]:
            st.success("Correct!", icon="✅")
        else:
            st.error("Not quite. The correct answer is marked below.", icon="❌")
        for a in answers:
            picked = a["text"] in attempt["selected"]
            icon = (":green[:material/check_circle:]" if a["isCorrect"]
                    else ":red[:material/cancel:]" if picked else ":gray[:material/radio_button_unchecked:]")
            text = md(a["text"])
            st.markdown(f"{icon} {f'**{text}**' if a['isCorrect'] else text}"
                        + (" — *your answer*" if picked else ""))
            if a["explanation"]:
                st.caption(md(a["explanation"]))

# ------------------------------------------------
# Navigation
# ------------------------------------------------
prev_col, _, next_col = st.columns([1, 2, 1])
if prev_col.button("Previous", icon=":material/arrow_back:", width="stretch", disabled=i == 0, shortcut="P"):
    st.session_state.index -= 1
    st.rerun()
if next_col.button("Next", icon=":material/arrow_forward:", icon_position="right", width="stretch",
                   type="primary" if attempt else "secondary", disabled=i == total - 1, shortcut="N"):
    st.session_state.index += 1
    st.rerun()
