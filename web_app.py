"""
YoungOnes Copy Web App — Streamlit interface.

Alternatief voor de Slack bot: open in de browser, vul een form in, krijg copy terug.
Zelfde copywriter.py backend als de Slack bot — zelfde skill files, zelfde kwaliteit.

Starten: streamlit run web_app.py
"""

import os
import streamlit as st

# Streamlit Cloud levert secrets via st.secrets — zet die in de omgeving
# zodat copywriter.py (en de Anthropic client) ze oppikken via os.environ.
if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

import copywriter

# ── Pagina-configuratie ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="YoungOnes Copywriter",
    page_icon="✍️",
    layout="centered",
)

# ── Styling ──────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* YoungOnes kleurenpalet */
    :root {
        --yo-orange: #FF5A1F;
        --yo-black: #111111;
        --yo-white: #FFFFFF;
        --yo-grey: #F5F5F5;
    }

    .stApp { background-color: var(--yo-white); }

    h1, h2, h3 { color: var(--yo-black); font-weight: 700; }

    .yo-header {
        background: var(--yo-black);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }

    .yo-header h1 {
        color: white;
        margin: 0;
        font-size: 1.6rem;
    }

    .yo-header p {
        color: #aaa;
        margin: 0.25rem 0 0 0;
        font-size: 0.9rem;
    }

    .copy-output {
        background: var(--yo-grey);
        border-left: 4px solid var(--yo-orange);
        padding: 1.25rem 1.5rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 1rem;
        white-space: pre-wrap;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    .stButton > button {
        background-color: var(--yo-orange) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 2rem !important;
        font-size: 1rem !important;
        transition: opacity 0.2s;
    }

    .stButton > button:hover { opacity: 0.85 !important; }

    .stTextArea textarea {
        border-radius: 8px !important;
        border: 1.5px solid #ddd !important;
        font-size: 0.95rem !important;
    }

    .stSelectbox > div > div {
        border-radius: 8px !important;
        border: 1.5px solid #ddd !important;
    }

    .chat-bubble-user {
        background: #eef2ff;
        border-radius: 12px 12px 4px 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.95rem;
    }

    .chat-bubble-bot {
        background: var(--yo-grey);
        border-radius: 12px 12px 12px 4px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.95rem;
        white-space: pre-wrap;
        line-height: 1.6;
    }

    .status-badge {
        display: inline-block;
        background: #e8f5e9;
        color: #2e7d32;
        border-radius: 20px;
        padding: 0.2rem 0.8rem;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="yo-header">
    <h1>YoungOnes Copywriter ✍️</h1>
    <p>Geef een briefing — krijg scherpe copy in de YoungOnes stem.</p>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

if "session" not in st.session_state:
    st.session_state.session = copywriter.create_session()
if "history" not in st.session_state:
    st.session_state.history = []  # lijst van (role, text) tuples
if "waiting_for_reply" not in st.session_state:
    st.session_state.waiting_for_reply = False

# ── Modus: form of chat ───────────────────────────────────────────────────────

mode = st.radio(
    "Hoe wil je starten?",
    ["Briefing form", "Vrije chat"],
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# MODUS 1: BRIEFING FORM
# ══════════════════════════════════════════════════════════════════════════════

if mode == "Briefing form":

    with st.form("briefing_form"):
        st.markdown("#### Jouw briefing")

        wat = st.text_area(
            "Wat schrijven we? *",
            placeholder="Bijv: een Instagram ad voor het zomerseizoen, gericht op studenten die willen bijverdienen",
            height=100,
        )

        col1, col2 = st.columns(2)

        with col1:
            doelgroep = st.selectbox(
                "Doelgroep",
                ["— kies —", "Werkenden (freelancers / flex)", "Opdrachtgevers (HR / managers)", "Beide"],
            )
            kanaal = st.selectbox(
                "Kanaal",
                ["— kies —", "Instagram ad", "LinkedIn post", "Facebook ad",
                 "Email", "Push notificatie", "Landingspagina", "Job post", "Overig"],
            )

        with col2:
            doel = st.selectbox(
                "Doel",
                ["— kies —", "Awareness", "Conversie / aanmelding", "Re-engagement",
                 "Vertrouwen opbouwen", "Retentie"],
            )
            toon = st.selectbox(
                "Toon (optioneel)",
                ["— laat de bot kiezen —", "Rebel / provocerend", "Emotioneel / herkenning",
                 "Rationeel / feiten", "Conversie / CTA-focus", "Mix"],
            )

        extra = st.text_area(
            "Extra context of eisen (optioneel)",
            placeholder="Bijv: max 125 tekens, gebruik de zin 'Werk op jouw manier', vermijd 'freelance'",
            height=70,
        )

        submitted = st.form_submit_button("Schrijf copy →", use_container_width=True)

    if submitted:
        if not wat.strip():
            st.error("Vul minimaal in wat we schrijven.")
        else:
            # Reset sessie voor elke nieuwe form-submit
            st.session_state.session = copywriter.create_session()
            st.session_state.history = []

            # Bouw de briefing op uit het form
            parts = [f"Schrijf copy voor YoungOnes. Briefing:\n\nWat: {wat.strip()}"]
            if doelgroep != "— kies —":
                parts.append(f"Doelgroep: {doelgroep}")
            if kanaal != "— kies —":
                parts.append(f"Kanaal: {kanaal}")
            if doel != "— kies —":
                parts.append(f"Doel: {doel}")
            if toon != "— laat de bot kiezen —":
                parts.append(f"Toon: {toon}")
            if extra.strip():
                parts.append(f"Extra eisen: {extra.strip()}")

            briefing = "\n".join(parts)
            st.session_state.history.append(("user", briefing))

            with st.spinner("Even nadenken..."):
                antwoord = copywriter.start_briefing(st.session_state.session, briefing)

            st.session_state.history.append(("bot", antwoord))
            st.session_state.waiting_for_reply = True
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MODUS 2: VRIJE CHAT
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "Vrije chat":
    st.markdown("#### Start met je briefing")
    st.caption("Typ wat je wil schrijven. De bot stelt vragen als hij meer info nodig heeft.")

    with st.form("first_message_form", clear_on_submit=True):
        first_msg = st.text_area(
            "Jouw briefing of vraag",
            placeholder="Bijv: ik wil een email schrijven voor werkenden die al een tijdje geen klus hebben gedaan",
            height=120,
            label_visibility="collapsed",
        )
        send = st.form_submit_button("Verstuur →", use_container_width=True)

    if send and first_msg.strip():
        st.session_state.session = copywriter.create_session()
        st.session_state.history = []
        st.session_state.history.append(("user", first_msg.strip()))

        with st.spinner("Even nadenken..."):
            antwoord = copywriter.start_briefing(st.session_state.session, first_msg.strip())

        st.session_state.history.append(("bot", antwoord))
        st.session_state.waiting_for_reply = True
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# GESPREKS-GESCHIEDENIS + REPLY
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.history:
    st.divider()
    st.markdown("#### Gesprek")

    for role, text in st.session_state.history:
        if role == "user":
            st.markdown(f'<div class="chat-bubble-user">👤 {text}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-bot">✍️ {text}</div>', unsafe_allow_html=True)

    # Copy-knop voor het laatste bot-bericht
    last_bot = next((t for r, t in reversed(st.session_state.history) if r == "bot"), None)
    if last_bot:
        st.code(last_bot, language=None)
        st.caption("↑ Selecteer en kopieer de copy hierboven")

    # Reply-veld voor vervolgvragen
    st.divider()
    st.markdown("#### Wil je iets aanpassen?")

    with st.form("reply_form", clear_on_submit=True):
        reply = st.text_area(
            "Jouw reactie",
            placeholder="Bijv: maak de rebel variant korter, pas aan voor LinkedIn, schrijf een A/B versie...",
            height=80,
            label_visibility="collapsed",
        )
        reply_sent = st.form_submit_button("Stuur →", use_container_width=True)

    if reply_sent and reply.strip():
        st.session_state.history.append(("user", reply.strip()))

        with st.spinner("Even nadenken..."):
            antwoord = copywriter.chat(st.session_state.session, reply.strip())

        st.session_state.history.append(("bot", antwoord))
        st.rerun()

    # Reset-knop
    st.divider()
    if st.button("Nieuwe briefing starten"):
        st.session_state.session = copywriter.create_session()
        st.session_state.history = []
        st.session_state.waiting_for_reply = False
        st.rerun()
