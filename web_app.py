"""
YoungOnes Copy Web App — Streamlit interface.
"""

import os
import re
import streamlit as st

if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

import copywriter

st.set_page_config(
    page_title="YoungOnes Copywriter",
    page_icon="✍️",
    layout="centered",
)

st.markdown("""
<style>
    .chat-bubble-user {
        background: #FFF0EB;
        border-left: 3px solid #FF5A1F;
        border-radius: 0 8px 8px 0;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.95rem;
        color: #111111;
    }
    .chat-bubble-bot {
        background: #F5F5F5;
        border-left: 3px solid #dddddd;
        border-radius: 0 8px 8px 0;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.95rem;
        white-space: pre-wrap;
        line-height: 1.6;
        color: #111111;
    }
    .variant-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #FF5A1F;
        margin-bottom: 0.4rem;
    }
    .approved-badge {
        display: inline-block;
        background: #E8F5E9;
        color: #2E7D32;
        border-radius: 20px;
        padding: 0.15rem 0.6rem;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

for key, default in {
    "session": None,
    "history": [],
    "last_briefing": {},
    "approved_ids": set(),  # set van copy-hashes die goedgekeurd zijn
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.session is None:
    st.session_state.session = copywriter.create_session()

# ── Variant parser ────────────────────────────────────────────────────────────

VARIANT_LABELS = [
    "AANBEVOLEN VERSIE",
    "REBEL VARIANT",
    "EMOTIONELE VARIANT",
    "RATIONELE VARIANT",
    "CONVERSIE VARIANT",
]

def parse_variants(text: str) -> list[dict]:
    variants = []
    pattern = "(" + "|".join(re.escape(l) for l in VARIANT_LABELS) + ")"
    parts = re.split(pattern, text)
    i = 0
    while i < len(parts):
        part = parts[i].strip()
        if part in VARIANT_LABELS and i + 1 < len(parts):
            body = parts[i + 1].strip()
            body = re.sub(r'\*Waarom:.*?\*', '', body, flags=re.DOTALL).strip()
            body = body.lstrip("-").strip()
            if body:
                variants.append({"label": part, "copy": body})
            i += 2
        else:
            i += 1
    if not variants and text.strip():
        variants.append({"label": "ANTWOORD", "copy": text.strip()})
    return variants

# ── UI ────────────────────────────────────────────────────────────────────────

st.title("YoungOnes Copywriter ✍️")
st.caption("Geef een briefing — krijg scherpe copy in de YoungOnes stem.")

mode = st.radio("Hoe wil je starten?", ["Briefing form", "Vrije chat"],
                horizontal=True, label_visibility="collapsed")
st.divider()

# ── Briefing form ─────────────────────────────────────────────────────────────

if mode == "Briefing form":
    with st.form("briefing_form"):
        st.markdown("#### Jouw briefing")
        wat = st.text_area("Wat schrijven we? *",
            placeholder="Bijv: een Instagram ad voor het zomerseizoen, gericht op studenten die willen bijverdienen",
            height=100)
        col1, col2 = st.columns(2)
        with col1:
            doelgroep = st.selectbox("Doelgroep", ["— kies —",
                "Werkenden (freelancers / flex)", "Opdrachtgevers (HR / managers)", "Beide"])
            kanaal = st.selectbox("Kanaal", ["— kies —",
                "Instagram ad", "LinkedIn post", "Facebook ad", "Email",
                "Push notificatie", "Landingspagina", "Job post", "Overig"])
        with col2:
            doel = st.selectbox("Doel", ["— kies —",
                "Awareness", "Conversie / aanmelding", "Re-engagement",
                "Vertrouwen opbouwen", "Retentie"])
            toon = st.selectbox("Toon", ["— laat de bot kiezen —",
                "Rebel / provocerend", "Emotioneel / herkenning",
                "Rationeel / feiten", "Conversie / CTA-focus", "Mix"])
        extra = st.text_area("Extra context (optioneel)",
            placeholder="Bijv: max 125 tekens, vermijd het woord 'freelance'", height=70)
        submitted = st.form_submit_button("Schrijf copy →", use_container_width=True)

    if submitted:
        if not wat.strip():
            st.error("Vul minimaal in wat we schrijven.")
        else:
            st.session_state.session = copywriter.create_session()
            st.session_state.history = []
            st.session_state.approved_ids = set()
            parts = [f"Schrijf copy voor YoungOnes.\n\nWat: {wat.strip()}"]
            if doelgroep != "— kies —": parts.append(f"Doelgroep: {doelgroep}")
            if kanaal != "— kies —": parts.append(f"Kanaal: {kanaal}")
            if doel != "— kies —": parts.append(f"Doel: {doel}")
            if toon != "— laat de bot kiezen —": parts.append(f"Toon: {toon}")
            if extra.strip(): parts.append(f"Extra: {extra.strip()}")
            briefing = "\n".join(parts)
            st.session_state.last_briefing = {"briefing": wat.strip(), "kanaal": kanaal, "doelgroep": doelgroep}
            st.session_state.history.append(("user", briefing))
            with st.spinner("Even nadenken..."):
                antwoord = copywriter.start_briefing(st.session_state.session, briefing)
            st.session_state.history.append(("bot", antwoord))
            st.rerun()

# ── Vrije chat ────────────────────────────────────────────────────────────────

elif mode == "Vrije chat":
    st.markdown("#### Start met je briefing")
    with st.form("first_message_form", clear_on_submit=True):
        first_msg = st.text_area("Jouw briefing",
            placeholder="Bijv: ik wil een email schrijven voor werkenden die al een tijdje geen klus hebben gedaan",
            height=120, label_visibility="collapsed")
        send = st.form_submit_button("Verstuur →", use_container_width=True)
    if send and first_msg.strip():
        st.session_state.session = copywriter.create_session()
        st.session_state.history = []
        st.session_state.approved_ids = set()
        st.session_state.last_briefing = {"briefing": first_msg.strip(), "kanaal": "", "doelgroep": ""}
        st.session_state.history.append(("user", first_msg.strip()))
        with st.spinner("Even nadenken..."):
            antwoord = copywriter.start_briefing(st.session_state.session, first_msg.strip())
        st.session_state.history.append(("bot", antwoord))
        st.rerun()

# ── Gesprekshistorie ──────────────────────────────────────────────────────────

if st.session_state.history:
    st.divider()

    for idx, (role, text) in enumerate(st.session_state.history):
        if role == "user":
            display = text.split("\n")[0].replace("Schrijf copy voor YoungOnes.", "").replace("Wat:", "").strip()
            st.markdown(f'<div class="chat-bubble-user">👤 {display or text}</div>', unsafe_allow_html=True)
        else:
            is_last = (idx == len(st.session_state.history) - 1)
            variants = parse_variants(text)
            has_variants = any(v["label"] in VARIANT_LABELS for v in variants)

            if is_last and has_variants:
                st.markdown("**✍️ Copy-pakket:**")
                for v_idx, variant in enumerate(variants):
                    copy_id = hash(variant["copy"])
                    already = copy_id in st.session_state.approved_ids
                    st.markdown(f'<div class="variant-label">{variant["label"]}</div>', unsafe_allow_html=True)
                    st.code(variant["copy"], language=None)
                    if already:
                        st.markdown('<span class="approved-badge">⭐ Goedgekeurd</span>', unsafe_allow_html=True)
                    else:
                        if st.button("👍 Goedkeuren", key=f"approve_{idx}_{v_idx}"):
                            st.session_state.approved_ids.add(copy_id)
                            st.rerun()
            else:
                st.markdown(f'<div class="chat-bubble-bot">✍️ {text}</div>', unsafe_allow_html=True)

    # Reply
    st.divider()
    with st.form("reply_form", clear_on_submit=True):
        reply = st.text_area("Wil je iets aanpassen?",
            placeholder="Bijv: maak de rebel variant korter, pas aan voor LinkedIn, schrijf een A/B versie...",
            height=80, label_visibility="collapsed")
        reply_sent = st.form_submit_button("Stuur →", use_container_width=True)
    if reply_sent and reply.strip():
        st.session_state.history.append(("user", reply.strip()))
        with st.spinner("Even nadenken..."):
            antwoord = copywriter.chat(st.session_state.session, reply.strip())
        st.session_state.history.append(("bot", antwoord))
        st.rerun()

    st.divider()
    if st.button("Nieuwe briefing starten"):
        st.session_state.session = copywriter.create_session()
        st.session_state.history = []
        st.session_state.approved_ids = set()
        st.session_state.last_briefing = {}
        st.rerun()
