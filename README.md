# YoungOnes Copy Bot

Slack-bot die het hele team copy laat schrijven via Claude (claude-opus-4-6).
Tag `@YoungOnesCopy` in elk kanaal → bot stelt vragen → levert 4 copy-varianten.

---

## Architectuur: één bron, twee ingangen

```
youngones-copywriter/
└── skills/youngones-copywriter/
    └── references/
        ├── brand-voice.md        ← officiële tone of voice + woordkeuzes
        ├── copy-examples.md      ← echte YoungOnes copy als kalibratie
        ├── psychological-principles.md
        └── copy-formats.md
              │
              ├── geladen door Claude Code skill (voor Lennart / Claude Code gebruikers)
              │
              └── geladen door deze Slack bot (voor het hele team)
```

**Één update aan de skill files → beide interfaces verbeteren automatisch.**
Er is geen dubbel te onderhouden systeem prompt.

---

## Hoe het team het gebruikt

### Via Slack (iedereen)

Tag `@YoungOnesCopy` in een kanaal met je briefing:

```
@YoungOnesCopy Schrijf een Instagram ad voor YoungOnes gericht op studenten
die willen bijverdienen. Focus op vrijheid en snel geld.
```

De bot:
1. Stelt 1-5 verduidelijkende vragen in de thread (als nodig)
2. Genereert een copy-pakket: aanbevolen versie + 4 varianten (rebel, emotioneel, rationeel, conversie)
3. Blijft itereren in dezelfde thread — vraag gerust om aanpassingen

**Itereren:**
Reply gewoon in de thread:
```
Maak de rebel variant korter en voeg urgentie toe
Pas aan voor LinkedIn in plaats van Instagram
Schrijf een A/B-versie van de aanbevolen variant
```

### Via Claude Code (Lennart / Claude Code gebruikers)

Gewoon typen in een sessie — de skill pikt het automatisch op:
```
Schrijf een email voor werkenden die al lang geen klus hebben gedaan
```

---

## Lokale setup

### 1. Maak een Slack App (eenmalig, ~10 min)

1. Ga naar [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. Naam: `YoungOnesCopy`, workspace: YoungOnes

**Socket Mode** (onder "Socket Mode"):
- Enable Socket Mode: **aan**
- App-Level Token aanmaken met scope `connections:write` → sla op als `SLACK_APP_TOKEN`

**Bot Token Scopes** (onder "OAuth & Permissions" → "Bot Token Scopes"):
```
app_mentions:read
chat:write
channels:history
groups:history
im:history
mpim:history
```

**Event Subscriptions** (onder "Event Subscriptions"):
- Enable Events: **aan**
- Subscribe to bot events: `app_mention`, `message.channels`, `message.groups`, `message.im`

**Installeren** (onder "OAuth & Permissions"):
- Install to Workspace → kopieer **Bot User OAuth Token** → sla op als `SLACK_BOT_TOKEN`

---

### 2. Environment variabelen

```bash
cd youngones-copy-bot
cp .env.example .env
```

Vul in `.env`:
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
ANTHROPIC_API_KEY=sk-ant-...
```

Het pad naar de skill files wordt automatisch gevonden als de mappen naast elkaar staan:
```
~/
├── youngones-copywriter/   ← skill files
└── youngones-copy-bot/     ← deze bot
```

Staat de skill map ergens anders? Voeg toe aan `.env`:
```
YOUNGONES_SKILL_DIR=/absoluut/pad/naar/youngones-copywriter/skills/youngones-copywriter
```

---

### 3. Installeer en start

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Bij opstarten zie je welke skill files geladen zijn:
```
[copywriter] Skill files geladen: references/brand-voice.md, references/copy-examples.md, ...
YoungOnes Copy Bot gestart. Wachten op mentions...
```

---

### 4. Bot toevoegen aan kanalen

In Slack: ga naar het kanaal → `/invite @YoungOnesCopy`

---

## De skill files updaten

De bot laadt de skill files bij **opstarten**. Na een update:

```bash
# Lokaal: restart de bot
^C
python app.py

# Op een server (pm2):
pm2 restart youngones-copy-bot
```

Welke bestanden bepalen het gedrag:

| Bestand | Wat het doet |
|---------|-------------|
| `brand-voice.md` | Toon, woordkeuzes, do's & don'ts |
| `copy-examples.md` | Echte YoungOnes copy als kalibratie |
| `psychological-principles.md` | AIDA, PAS, Cialdini etc. |
| `copy-formats.md` | Instagram, email, push, LinkedIn formats |

---

## Deployment (24/7, zonder laptop)

### Railway / Render / Fly.io (makkelijkst)

1. Push deze map naar een private GitHub repo
2. Maak een nieuw project aan op Railway/Render
3. Stel environment variables in via het dashboard
4. Stel `YOUNGONES_SKILL_DIR` in op het absolute pad waar je de skill files neergezet hebt op de server, of kopieer de `references/` map mee naar de repo

**Tip:** Voeg de `references/` map toe aan de repo zodat ze altijd meereizen:
```bash
cp -r ../youngones-copywriter/skills/youngones-copywriter/references ./references
```
En pas de env var aan:
```
YOUNGONES_SKILL_DIR=./references  # of het absolute pad op de server
```

### VPS (DigitalOcean, Hetzner)

```bash
npm install -g pm2
pm2 start app.py --interpreter python3 --name youngones-copy-bot
pm2 save
pm2 startup  # auto-start na reboot
```

---

## Bestanden

```
youngones-copy-bot/
├── app.py          ← Slack Bolt bot (Socket Mode, per-thread sessies)
├── copywriter.py   ← Claude API + skill file loader
├── requirements.txt
├── .env.example
└── README.md
```
