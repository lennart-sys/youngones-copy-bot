"""
YoungOnes Copy Web App — Streamlit interface.

Twee modi:
- Briefing form / vrije chat → copy genereren
- Review tab → goedgekeurde copy exporteren naar copy-examples.md
"""

import os
import re
import datetime
import streamlit as st

if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

import copywriter

# ── Pagina-configuratie ──────────────────────────────────────────────────────

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
    .variant-card {
        background: #F5F5F5;
        border: 1.5px solid #E0E0E0;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
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
    "approved": [],        # lijst van dicts: {label, copy, briefing, kanaal, doelgroep}
    "last_briefing": {},   # context van de laatste briefing voor export
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
    """
    Extraheer individuele copy-varianten uit de bot-output.
    Geeft een lijst van {label, copy} dicts terug.
    Als parsing mislukt, geef de volledige tekst terug als één blok.
    """
    variants = []
    pattern = "(" + "|".join(re.escape(l) for l in VARIANT_LABELS) + ")"
    parts = re.split(pattern, text)

    i = 0
    while i < len(parts):
        part = parts[i].strip()
        if part in VARIANT_LABELS and i + 1 < len(parts):
            label = part
            body = parts[i + 1].strip()
            # Verwijder italic rationale (*Waarom: ...*) uit aanbevolen versie
            body = re.sub(r'\*Waarom:.*?\*', '', body, flags=re.DOTALL).strip()
            # Strip leading dashes/dividers
            body = body.lstrip("-").strip()
            if body:
                variants.append({"label": label, "copy": body})
            i += 2
        else:
            i += 1

    # Fallback: geen varianten gevonden → toon als geheel
    if not variants and text.strip():
        variants.append({"label": "ANTWOORD", "copy": text.strip()})

    return variants


def export_markdown(approved: list[dict]) -> str:
    """Genereer een markdown-blok klaar om in copy-examples.md te plakken."""
    datum = datetime.date.today().strftime("%d-%m-%Y")
    lines = [f"\n\n## Goedgekeurde copy — toegevoegd {datum}\n"]
    for item in approved:
        lines.append(f"### {item['label']}")
        if item.get("briefing"):
            lines.append(f"**Briefing:** {item['briefing']}")
        if item.get("kanaal"):
            lines.append(f"**Kanaal:** {item['kanaal']}")
        if item.get("doelgroep"):
            lines.append(f"**Doelgroep:** {item['doelgroep']}")
        lines.append(f"\n```\n{item['copy']}\n```")
        if item.get("notitie"):
            lines.append(f"\n*Waarom het werkt: {item['notitie']}*")
        lines.append("")
    return "\n".join(lines)


# ── Navigatie ─────────────────────────────────────────────────────────────────

tab_copy, tab_review = st.tabs(["✍️ Copy schrijven", f"⭐ Review ({len(st.session_state.approved)} goedgekeurd)"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: COPY SCHRIJVEN
# ══════════════════════════════════════════════════════════════════════════════

with tab_copy:
    st.title("YoungOnes Copywriter ✍️")
    st.caption("Geef een briefing — krijg scherpe copy in de YoungOnes stem.")

    mode = st.radio("Hoe wil je starten?", ["Briefing form", "Vrije chat"],
                    horizontal=True, label_visibility="collapsed")
    st.divider()

    # ── Briefing form ──────────────────────────────────────────────────────────
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
                parts = [f"Schrijf copy voor YoungOnes.\n\nWat: {wat.strip()}"]
                if doelgroep != "— kies —": parts.append(f"Doelgroep: {doelgroep}")
                if kanaal != "— kies —": parts.append(f"Kanaal: {kanaal}")
                if doel != "— kies —": parts.append(f"Doel: {doel}")
                if toon != "— laat de bot kiezen —": parts.append(f"Toon: {toon}")
                if extra.strip(): parts.append(f"Extra: {extra.strip()}")
                briefing = "\n".join(parts)

                # Sla context op voor export
                st.session_state.last_briefing = {
                    "briefing": wat.strip(),
                    "kanaal": kanaal if kanaal != "— kies —" else "",
                    "doelgroep": doelgroep if doelgroep != "— kies —" else "",
                }
                st.session_state.history.append(("user", briefing))
                with st.spinner("Even nadenken..."):
                    antwoord = copywriter.start_briefing(st.session_state.session, briefing)
                st.session_state.history.append(("bot", antwoord))
                st.rerun()

    # ── Vrije chat ─────────────────────────────────────────────────────────────
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
            st.session_state.last_briefing = {"briefing": first_msg.strip(), "kanaal": "", "doelgroep": ""}
            st.session_state.history.append(("user", first_msg.strip()))
            with st.spinner("Even nadenken..."):
                antwoord = copywriter.start_briefing(st.session_state.session, first_msg.strip())
            st.session_state.history.append(("bot", antwoord))
            st.rerun()

    # ── Gesprekshistorie ───────────────────────────────────────────────────────
    if st.session_state.history:
        st.divider()

        for idx, (role, text) in enumerate(st.session_state.history):
            if role == "user":
                # Laat de ruwe briefing string niet zien als hij van het form komt
                display = text.split("\n")[0].replace("Schrijf copy voor YoungOnes.", "").replace("Wat:", "").strip()
                st.markdown(f'<div class="chat-bubble-user">👤 {display or text}</div>',
                            unsafe_allow_html=True)
            else:
                # Probeer varianten te parsen voor het laatste bot-bericht
                is_last_bot = (idx == len(st.session_state.history) - 1)
                variants = parse_variants(text)
                has_variants = len(variants) > 1 or (len(variants) == 1 and variants[0]["label"] != "ANTWOORD")

                if is_last_bot and has_variants:
                    # Toon elke variant als kaart met 👍-knop
                    st.markdown("**✍️ Copy-pakket:**")
                    for v_idx, variant in enumerate(variants):
                        already_approved = any(
                            a["copy"] == variant["copy"] for a in st.session_state.approved
                        )
                        with st.container():
                            st.markdown(f'<div class="variant-label">{variant["label"]}</div>',
                                        unsafe_allow_html=True)
                            st.code(variant["copy"], language=None)
                            if already_approved:
                                st.markdown('<span class="approved-badge">⭐ Goedgekeurd</span>',
                                            unsafe_allow_html=True)
                            else:
                                if st.button(f"👍 Goedkeuren", key=f"approve_{idx}_{v_idx}"):
                                    st.session_state.approved.append({
                                        "label": variant["label"],
                                        "copy": variant["copy"],
                                        "briefing": st.session_state.last_briefing.get("briefing", ""),
                                        "kanaal": st.session_state.last_briefing.get("kanaal", ""),
                                        "doelgroep": st.session_state.last_briefing.get("doelgroep", ""),
                                        "notitie": "",
                                    })
                                    st.rerun()
                else:
                    # Geen varianten (bijv. vervolgvraag) → toon als chatbubble
                    st.markdown(f'<div class="chat-bubble-bot">✍️ {text}</div>',
                                unsafe_allow_html=True)

        # Reply-veld
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
            st.session_state.last_briefing = {}
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: REVIEW — GOEDGEKEURDE COPY EXPORTEREN
# ══════════════════════════════════════════════════════════════════════════════

with tab_review:
    st.title("⭐ Goedgekeurde copy")
    st.caption("Keur copy goed in het 'Copy schrijven' tabblad. Voeg hier context toe en exporteer naar copy-examples.md.")

    if not st.session_state.approved:
        st.info("Nog geen copy goedgekeurd. Ga naar 'Copy schrijven', genereer copy en klik op 👍 bij een variant.")
    else:
        st.markdown(f"**{len(st.session_state.approved)} variant(en) goedgekeurd** — voeg context toe en exporteer.")
        st.divider()

        to_remove = []
        for i, item in enumerate(st.session_state.approved):
            with st.expander(f"**{item['label']}** — {item['briefing'][:60]}..." if len(item['briefing']) > 60 else f"**{item['label']}** — {item['briefing']}", expanded=True):
                st.code(item["copy"], language=None)

                col1, col2 = st.columns(2)
                with col1:
                    item["kanaal"] = st.text_input("Kanaal", value=item["kanaal"],
                        key=f"kanaal_{i}", placeholder="bijv. Instagram ad")
                with col2:
                    item["doelgroep"] = st.text_input("Doelgroep", value=item["doelgroep"],
                        key=f"dg_{i}", placeholder="bijv. Werkenden")

                item["notitie"] = st.text_input(
                    "Waarom werkt dit? (optioneel — wordt meegenomen in copy-examples.md)",
                    value=item.get("notitie", ""),
                    key=f"notitie_{i}",
                    placeholder="bijv. Contrarian hook + specifiek getal werkt goed voor awareness"
                )

                if st.button("🗑️ Verwijderen", key=f"remove_{i}"):
                    to_remove.append(i)

        for i in reversed(to_remove):
            st.session_state.approved.pop(i)
        if to_remove:
            st.rerun()

        st.divider()
        st.markdown("### Exporteren naar copy-examples.md")
        st.caption("Download het bestand, open `copy-examples.md` in je editor, plak onderaan, sla op en push naar GitHub.")

        md_content = export_markdown(st.session_state.approved)

        st.download_button(
            label="⬇️ Download als .md snippet",
            data=md_content,
            file_name=f"youngones-copy-{datetime.date.today().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

        with st.expander("Preview van de export"):
            st.code(md_content, language="markdown")

        st.divider()
        st.markdown("**Na het plakken en opslaan — terminal:**")
        st.code("""cd /Users/lennartvanderaa/youngones-copy-bot
cp /Users/lennartvanderaa/youngones-copywriter/skills/youngones-copywriter/references/copy-examples.md references/copy-examples.md
git add references/copy-examples.md
git commit -m "Add approved copy examples"
git push""", language="bash")

        if st.button("🗑️ Wis alle goedgekeurde copy", type="secondary"):
            st.session_state.approved = []
            st.rerun()
