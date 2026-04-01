"""
YoungOnes Copywriter — Claude API conversation logic.

System prompt wordt dynamisch samengesteld vanuit de skill reference files.
Zo is er één bron van waarheid: update de skill files → beide interfaces verbeteren.
"""

import os
import anthropic
from pathlib import Path

client = anthropic.Anthropic()

# Pad naar de skill reference files.
# Volgorde van prioriteit:
# 1. YOUNGONES_SKILL_DIR env var (als die gezet is)
# 2. references/ map naast dit bestand (voor Streamlit Cloud en deployment)
# 3. Zustermap youngones-copywriter (voor lokale dev met beide repos naast elkaar)
_local_references = Path(__file__).parent / "references"
_sibling_skill = Path(__file__).parent.parent / "youngones-copywriter" / "skills" / "youngones-copywriter"

SKILL_DIR = Path(
    os.environ.get("YOUNGONES_SKILL_DIR")
    or (_local_references if _local_references.exists() else _sibling_skill)
)

REFERENCE_FILES = [
    "references/brand-voice.md",
    "references/copy-examples.md",
    "references/psychological-principles.md",
    "references/copy-formats.md",
]

SYSTEM_PROMPT_HEADER = """Je bent de YoungOnes Copywriter — de copywriting-assistent voor het marketingteam van YoungOnes.

Hieronder vind je de volledige YoungOnes brand voice gids, echte voorbeeldcopy, psychologische principes en kanaalformats. Gebruik dit als je kalibratie bij elke tekst die je schrijft.

---

"""

SYSTEM_PROMPT_FOOTER = """

---

## Jouw aanpak bij een briefing

Stel maximaal 5 gerichte vragen om de briefing compleet te maken. Eén vraag tegelijk. Wacht op antwoord. Zodra je genoeg weet, genereer je het copy-pakket.

Essentiële info die je nodig hebt (als die er nog niet in zit):
1. **Wat?** — product, feature, campagne, actie
2. **Voor wie?** — werkenden of opdrachtgevers? Segment?
3. **Doel?** — awareness, conversie, re-engagement, vertrouwen
4. **Kanaal?** — Instagram, LinkedIn, email, push, landingspagina, job post
5. **Toon?** — rebel, emotioneel, rationeel, conversie (of mix)

Als de briefing al voldoende info bevat, ga je direct naar copy genereren.

## Copy-pakket format

Lever altijd dit pakket:

---
**AANBEVOLEN VERSIE** *(beste match voor doel + kanaal)*
[copy hier]
*Waarom: [1 zin rationale]*

---
**REBEL VARIANT** *(provocerend, stopt de scroll)*
[copy hier]

**EMOTIONELE VARIANT** *(herkenning, verlangen)*
[copy hier]

**RATIONELE VARIANT** *(feiten, voordelen, bezwaar-weerlegging)*
[copy hier]

**CONVERSIE VARIANT** *(CTA-focus, urgentie, laagdrempelig)*
[copy hier]

---
*Wil je een variant uitwerken, aanpassen voor een ander kanaal, of een A/B-set?*
"""


def _load_references() -> str:
    """Lees de skill reference files en combineer ze tot één string."""
    parts = []
    for filename in REFERENCE_FILES:
        path = SKILL_DIR / filename
        if path.exists():
            content = path.read_text(encoding="utf-8")
            parts.append(f"## {path.stem.replace('-', ' ').title()}\n\n{content}")
        else:
            # Stille fallback — bot werkt ook zonder een ontbrekend bestand
            parts.append(f"<!-- {filename} niet gevonden op {path} -->")
    return "\n\n---\n\n".join(parts)


def build_system_prompt() -> str:
    """Bouw het volledige system prompt op vanuit de skill files."""
    references = _load_references()
    return SYSTEM_PROMPT_HEADER + references + SYSTEM_PROMPT_FOOTER


# Laad het system prompt eenmalig bij opstarten.
# Herstart de bot om updates in skill files op te pikken.
SYSTEM_PROMPT = build_system_prompt()

# Log welke bestanden geladen zijn
_loaded = [f for f in REFERENCE_FILES if (SKILL_DIR / f).exists()]
_missing = [f for f in REFERENCE_FILES if not (SKILL_DIR / f).exists()]
if _loaded:
    print(f"[copywriter] Skill files geladen: {', '.join(_loaded)}")
if _missing:
    print(f"[copywriter] Skill files niet gevonden (wordt overgeslagen): {', '.join(_missing)}")


def create_session() -> dict:
    """Start een nieuwe copywriting-sessie."""
    return {"messages": []}


def chat(session: dict, user_message: str) -> str:
    """
    Verwerk een gebruikersbericht en geef Claude's antwoord terug.
    Stuurt de volledige gesprekshistorie mee voor multi-turn context.
    """
    session["messages"].append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=session["messages"],
    )

    assistant_text = next(
        (block.text for block in response.content if block.type == "text"),
        "Er ging iets mis bij het genereren van de copy.",
    )

    session["messages"].append({"role": "assistant", "content": assistant_text})
    return assistant_text


def start_briefing(session: dict, initial_message: str) -> str:
    """
    Verwerk het eerste bericht in een sessie.
    Als de briefing al compleet is, schrijf direct copy.
    Anders: stel de eerste ontbrekende vraag.
    """
    prompt = (
        f'De gebruiker wil copy laten schrijven. Dit is hun bericht:\n\n"{initial_message}"\n\n'
        "Analyseer of je al genoeg info hebt.\n"
        "- Genoeg info: genereer direct het volledige copy-pakket.\n"
        "- Meer info nodig: stel de EERSTE ontbrekende vraag. Één vraag. Geen inleiding."
    )
    return chat(session, prompt)
