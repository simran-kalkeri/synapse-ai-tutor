"""
Assessment Page for Synapse AI Tutor.
15-question format: 5 Easy (1pt) + 5 Intermediate (2pt) + 5 Hard (3pt).
Max score per topic = 30. Supports assessment reuse and multi-topic queue.
"""

import streamlit as st
from backend.assessment import (
    load_dataset, categorize_questions,
    select_assessment_questions, calculate_score
)
from backend.progress_tracker import (
    update_assessment_score, get_topic_progress,
    topic_is_assessed, update_knowledge_gaps
)
from backend.gap_detector import detect_knowledge_gaps as detect_gaps


# Hex values for inline styles — chosen for good contrast in both themes
DIFF_COLORS = {"easy": "#059669", "intermediate": "#D97706", "hard": "#6366F1"}
DIFF_LABELS = {"easy": "Easy  (1 pt)", "intermediate": "Intermediate  (2 pts)", "hard": "Hard  (3 pts)"}


def _ensure_question_bank():
    if st.session_state.topic_banks is None:
        with st.spinner("Loading question bank..."):
            questions = load_dataset()
            st.session_state.topic_banks = categorize_questions(questions)


def _ensure_assessment_questions(topic):
    if st.session_state.assessment_questions is None:
        _ensure_question_bank()
        qs = select_assessment_questions(st.session_state.topic_banks, topic)
        st.session_state.assessment_questions = qs
        st.session_state.assessment_answers = [None] * len(qs)
        st.session_state.current_question_idx = 0
        st.session_state.assessment_complete = False


def render_assessment():
    if not st.session_state.selected_topic:
        st.warning("Please select a topic first.")
        if st.button("Go to Topics"):
            st.session_state.page = "topic_selection"
            st.rerun()
        return

    topic = st.session_state.selected_topic
    username = st.session_state.username

    # ── Assessment Reuse Gate ────────────────────────────────────────────────
    if topic_is_assessed(username, topic) and st.session_state.assessment_questions is None and not st.session_state.assessment_complete:
        _render_existing_profile(topic, username)
        return

    # Header
    h_col1, h_col2 = st.columns([3, 1])
    with h_col1:
        st.markdown(f"""
        <div class="main-header animate-fade-in" style="text-align:left; padding: 1rem 0;">
            <h1 style="margin-bottom:0.2rem; font-size: 2rem;">Assessment</h1>
            <p style="color:var(--text-secondary); margin:0;">Topic: <strong style="color:var(--primary);">{topic}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    with h_col2:
        st.write("") # spacer
        focus_label = "🔍 Exit Focus" if st.session_state.get("focus_mode") else "🎯 Focus Mode"
        if st.button(focus_label, use_container_width=True, key="focus_assess"):
            st.session_state.focus_mode = not st.session_state.get("focus_mode", False)
            st.rerun()

    # Progress through multi-topic queue
    queue = st.session_state.get("topic_queue", [])
    q_idx = st.session_state.get("topic_queue_idx", 0)
    if len(queue) > 1:
        st.markdown(f"""
        <div style="text-align:right;color:var(--text-secondary);font-size:0.8rem;margin-bottom:0.5rem;">
            Topic {q_idx+1} of {len(queue)}: assessing <strong style="color:var(--primary);">{topic}</strong>
        </div>""", unsafe_allow_html=True)

    _ensure_assessment_questions(topic)
    questions = st.session_state.assessment_questions

    if st.session_state.assessment_complete:
        _render_results(topic, username)
    else:
        _render_questions(questions, topic)


def _render_existing_profile(topic, username):
    """Show existing profile and offer Retake / Continue."""
    progress = get_topic_progress(username, topic)
    mastery = progress.get("mastery", 0)
    level = progress.get("level", "Not Assessed")
    score = progress.get("score", 0)
    max_score = progress.get("max_score", 30)
    gaps = progress.get("knowledge_gaps", [])
    history = progress.get("assessment_history", [])

    lc = {"Beginner": "#2ECC71", "Intermediate": "#F39C12", "Advanced": "#8B83FF"}.get(level, "#A0A0C0")

    st.markdown(f"""
    <div class="main-header animate-fade-in" style="text-align:left;">
        <h1>Assessment</h1>
        <p style="color:var(--text-secondary);">Topic: <strong style="color:var(--primary);">{topic}</strong></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="synapse-card animate-fade-in" style="text-align:center;padding:2rem;">
        <div style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:0.8rem;">Previous Assessment Result</div>
        <div style="display:flex;justify-content:center;gap:3rem;margin-bottom:1.5rem;">
            <div>
                <div style="font-size:2.5rem;font-weight:800;color:{lc};">{score}/{max_score}</div>
                <div style="color:var(--text-secondary);font-size:0.8rem;">Score (raw)</div>
            </div>
            <div>
                <div style="font-size:2.5rem;font-weight:800;color:{lc};">{mastery}%</div>
                <div style="color:var(--text-secondary);font-size:0.8rem;">Mastery</div>
            </div>
        </div>
        <div style="display:inline-block;padding:0.4rem 1.2rem;border-radius:var(--radius-pill);
                    background:rgba({_hex_to_rgb(lc)},0.15);border:1px solid rgba({_hex_to_rgb(lc)},0.3);
                    color:{lc};font-weight:700;font-size:1rem;">{level}</div>
    </div>
    """, unsafe_allow_html=True)

    # Knowledge gaps
    if gaps:
        st.markdown("""
        <div class="gap-warning" style="margin-top:1rem;">
            <div style="color:var(--warning);font-weight:600;margin-bottom:0.4rem;">Knowledge Gaps</div>
        """, unsafe_allow_html=True)
        for g in gaps[:6]:
            st.markdown(f"<div style='color:var(--text-secondary);font-size:0.85rem;margin:0.15rem 0;'>* {g}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.success("No knowledge gaps detected for this topic.")

    # Assessment history
    if history:
        with st.expander(f"Assessment History ({len(history)} attempts)"):
            for i, h in enumerate(reversed(history[-5:]), 1):
                date_str = h.get("date", "")[:10]
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:0.3rem 0.5rem;
                            background:var(--border-light);border-radius:var(--radius-sm);margin-bottom:0.2rem;">
                    <span style="color:var(--text-secondary);font-size:0.8rem;">Attempt {len(history)-i+1} &nbsp;({date_str})</span>
                    <span style="color:var(--text-primary);font-size:0.8rem;font-weight:600;">{h.get('score',0)}/{h.get('max_score',30)} &nbsp;–&nbsp; {h.get('level','')}</span>
                </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Continue Learning", use_container_width=True, type="primary"):
            if topic not in st.session_state.chat_histories:
                st.session_state.chat_histories[topic] = []
            st.session_state.page = "tutor"
            st.rerun()
    with col2:
        if st.button("Retake Assessment", use_container_width=True):
            # Force a fresh assessment
            st.session_state.assessment_questions = None
            st.session_state.assessment_answers = []
            st.session_state.assessment_complete = False
            st.session_state.assessment_result = None
            st.session_state.current_question_idx = 0
            st.rerun()
    with col3:
        if st.button("Choose Topics", use_container_width=True):
            st.session_state.page = "topic_selection"
            st.rerun()


def _render_questions(questions, topic):
    total = len(questions)
    current_idx = st.session_state.current_question_idx

    # Determine current difficulty section
    if current_idx < 5:
        diff = "easy"
        section_num = 1
    elif current_idx < 10:
        diff = "intermediate"
        section_num = 2
    else:
        diff = "hard"
        section_num = 3

    diff_color = DIFF_COLORS[diff]
    diff_label = DIFF_LABELS[diff]

    # Progress bar + section indicator
    progress_val = current_idx / total
    st.progress(progress_val, text=f"Question {current_idx+1} of {total}")

    # Section header
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:1rem;margin-top:0.5rem;">
        <div style="padding:0.3rem 0.9rem;border-radius:20px;background:rgba({_hex_to_rgb(diff_color)},0.12);
                    border:1px solid rgba({_hex_to_rgb(diff_color)},0.3);color:{diff_color};
                    font-weight:600;font-size:0.8rem;">Section {section_num}/3 — {diff_label}</div>
        <div style="color:#6B6B8D;font-size:0.78rem;">Max score: 30 pts</div>
    </div>
    """, unsafe_allow_html=True)

    if current_idx < total:
        q = questions[current_idx]
        pts = q.get("points", 1)

        st.markdown(f"""
        <div class="synapse-card animate-fade-in">
            <div style="display:flex;align-items:flex-start;gap:1rem;">
                <div style="background:linear-gradient(135deg,{diff_color},{diff_color}88);
                            border-radius:50%;width:38px;height:38px;display:flex;align-items:center;
                            justify-content:center;font-weight:700;color:white;flex-shrink:0;font-size:1rem;">
                    {current_idx+1}
                </div>
                <div>
                    <div style="color:#FFFFFF;font-size:1rem;font-weight:500;line-height:1.5;">{q['question']}</div>
                    <div style="color:{diff_color};font-size:0.72rem;margin-top:0.3rem;">{pts} point{"s" if pts > 1 else ""}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        selected = st.radio(
            "Select your answer:",
            options=range(len(q["options"])),
            format_func=lambda x: q["options"][x],
            key=f"q_{current_idx}_{topic}",
            index=None,
            label_visibility="collapsed"
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if current_idx > 0:
                if st.button("Previous", use_container_width=True):
                    st.session_state.current_question_idx -= 1
                    st.rerun()

        with col3:
            if current_idx < total - 1:
                if st.button("Next", use_container_width=True):
                    if selected is not None:
                        st.session_state.assessment_answers[current_idx] = selected
                    st.session_state.current_question_idx += 1
                    st.rerun()
            else:
                if st.button("Submit Assessment", use_container_width=True, type="primary"):
                    if selected is not None:
                        st.session_state.assessment_answers[current_idx] = selected

                    result = calculate_score(st.session_state.assessment_answers, questions)

                    # Detect knowledge gaps based on wrong answers
                    gaps = _compute_gaps_from_answers(
                        st.session_state.assessment_answers, questions, st.session_state.username, topic
                    )

                    # Save to persistent progress
                    update_assessment_score(
                        username=st.session_state.username,
                        topic=topic,
                        score=result["score"],
                        max_score=result["max_score"],
                        level=result["level"],
                        knowledge_gaps=gaps
                    )

                    result["knowledge_gaps"] = gaps
                    st.session_state.assessment_result = result
                    st.session_state.assessment_complete = True
                    st.rerun()

    # Question timeline indicators
    st.markdown("<br>", unsafe_allow_html=True)
    ind_cols = st.columns(total)
    for i in range(total):
        with ind_cols[i]:
            if i == current_idx:
                diff_key = "easy" if i < 5 else "intermediate" if i < 10 else "hard"
                dot_bg  = DIFF_COLORS[diff_key]
                dot_brd = f"2px solid {DIFF_COLORS[diff_key]}"
            elif st.session_state.assessment_answers[i] is not None:
                dot_bg  = "rgba(5,150,105,0.35)"
                dot_brd = "1.5px solid #059669"
            else:
                dot_bg  = "var(--border-light)"
                dot_brd = "1px solid var(--border)"
            st.markdown(
                f'<div style="width:100%;height:5px;background:{dot_bg};'
                f'border-radius:var(--radius-pill);border:{dot_brd};"></div>',
                unsafe_allow_html=True
            )


def _compute_gaps_from_answers(answers, questions, username, topic) -> list:
    """Detect gaps: pull prerequisite concepts for questions answered incorrectly."""
    from backend.gap_detector import PREREQUISITE_MAP
    prereqs = PREREQUISITE_MAP.get(topic, {}).get("prerequisites", [])
    key_concepts = PREREQUISITE_MAP.get(topic, {}).get("key_concepts", [])

    incorrect_diffs = []
    for i, q in enumerate(questions):
        if i >= len(answers) or answers[i] is None or answers[i] != q["correct_index"]:
            incorrect_diffs.append(q.get("difficulty", "intermediate"))

    # If many hard questions wrong → add key concepts as gaps
    hard_wrong = incorrect_diffs.count("hard")
    inter_wrong = incorrect_diffs.count("intermediate")
    easy_wrong = incorrect_diffs.count("easy")

    gaps = []
    if hard_wrong >= 3:
        gaps += key_concepts[:3]
    if inter_wrong >= 3:
        gaps += prereqs[:3]
    elif easy_wrong >= 3:
        gaps += prereqs[:2]

    # Remove duplicates
    seen = set()
    unique_gaps = []
    for g in gaps:
        if g not in seen:
            seen.add(g)
            unique_gaps.append(g)

    return unique_gaps


def _render_results(topic, username):
    result = st.session_state.assessment_result
    if not result:
        return

    score = result["score"]
    max_score = result["max_score"]
    level = result["level"]
    correct = result["correct"]
    total = result["total"]
    percentage = result["percentage"]
    gaps = result.get("knowledge_gaps", [])
    per_diff = result.get("per_difficulty", {})

    # Level color — semantic CSS variables
    lc_map = {
        "Beginner":     "var(--success)",
        "Intermediate": "var(--warning)",
        "Advanced":     "var(--primary)",
    }
    lc = lc_map.get(level, "var(--text-muted)")
    msg = {
        "Beginner":     "You're getting started! The tutor will teach from the ground up with clear explanations and analogies.",
        "Intermediate": "Good foundation! The tutor will build with technical examples and practical applications.",
        "Advanced":     "Excellent mastery! The tutor will engage with advanced discussions and research-level insights.",
    }.get(level, "")

    st.markdown(f"""
    <div class="synapse-card animate-fade-in" style="text-align:center;padding:2.5rem;">
        <h2 style="margin-bottom:0.5rem;">Assessment Complete!</h2>
        <p style="color:var(--text-secondary);margin-bottom:2rem;">
            Topic: <strong style="color:var(--primary);">{topic}</strong>
        </p>
        <div style="display:flex;justify-content:center;gap:3rem;margin-bottom:1.5rem;">
            <div>
                <div style="font-size:2.8rem;font-weight:800;color:{lc};
                            font-family:'Outfit',sans-serif;">{score}/{max_score}</div>
                <div style="color:var(--text-muted);font-size:0.82rem;">Raw Score</div>
            </div>
            <div>
                <div style="font-size:2.8rem;font-weight:800;color:{lc};
                            font-family:'Outfit',sans-serif;">{correct}/{total}</div>
                <div style="color:var(--text-muted);font-size:0.82rem;">Correct</div>
            </div>
        </div>
        <div style="display:inline-block;padding:0.4rem 1.25rem;
                    border-radius:var(--radius-pill);background:var(--primary-alpha);
                    border:1px solid var(--border);color:{lc};
                    font-weight:700;font-size:1rem;">{level}</div>
        <p style="color:var(--text-secondary);margin-top:1.2rem;font-size:0.875rem;
                  max-width:480px;margin-left:auto;margin-right:auto;">{msg}</p>
    </div>
    """, unsafe_allow_html=True)

    # Per-difficulty breakdown
    if per_diff:
        st.markdown("<br>", unsafe_allow_html=True)
        dcols = st.columns(3)
        for i, (diff, dc) in enumerate(per_diff.items()):
            if dc["total"] == 0:
                continue
            acc    = int((dc["correct"] / dc["total"]) * 100)
            dcolor = DIFF_COLORS.get(diff, "#94A3B8")
            with dcols[i]:
                st.markdown(f"""
                <div class="stat-card">
                    <div style="color:{dcolor};font-size:0.68rem;text-transform:uppercase;
                                font-weight:700;margin-bottom:0.3rem;letter-spacing:0.06em;">{diff}</div>
                    <div style="font-size:1.6rem;font-weight:800;color:{dcolor};
                                font-family:'Outfit',sans-serif;">{dc['correct']}/{dc['total']}</div>
                    <div style="color:var(--text-muted);font-size:0.75rem;
                                margin-top:0.15rem;">{acc}% accuracy</div>
                </div>""", unsafe_allow_html=True)

    # Knowledge gaps
    if gaps:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="gap-warning">
            <div style="color:var(--warning);font-weight:600;margin-bottom:0.4rem;">
                Knowledge Gaps Detected
            </div>
        """, unsafe_allow_html=True)
        for g in gaps:
            st.markdown(
                f"<div style='color:var(--text-secondary);font-size:0.85rem;margin:0.2rem 0;'>· {g}</div>",
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Multi-topic queue: advance to next topic or finish
    queue = st.session_state.get("topic_queue", [])
    q_idx = st.session_state.get("topic_queue_idx", 0)
    has_next = (q_idx + 1) < len(queue)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Start Tutoring", use_container_width=True, type="primary"):
            if topic not in st.session_state.chat_histories:
                st.session_state.chat_histories[topic] = []
            st.session_state.page = "tutor"
            st.rerun()

    with col2:
        if st.button("View Roadmap", use_container_width=True):
            st.session_state.page = "roadmap"
            st.rerun()

    with col3:
        if has_next:
            next_topic = queue[q_idx + 1]
            if st.button(f"Next: Assess {next_topic[:15]}", use_container_width=True):
                st.session_state.topic_queue_idx += 1
                st.session_state.selected_topic = next_topic
                st.session_state.assessment_questions = None
                st.session_state.assessment_answers = []
                st.session_state.assessment_complete = False
                st.session_state.assessment_result = None
                st.session_state.current_question_idx = 0
                st.rerun()
        else:
            if st.button("Retake Assessment", use_container_width=True):
                st.session_state.assessment_questions = None
                st.session_state.assessment_answers = []
                st.session_state.assessment_complete = False
                st.session_state.assessment_result = None
                st.session_state.current_question_idx = 0
                st.rerun()

    with col4:
        if st.button("Choose Topics", use_container_width=True):
            st.session_state.page = "topic_selection"
            st.rerun()


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip('#')
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
