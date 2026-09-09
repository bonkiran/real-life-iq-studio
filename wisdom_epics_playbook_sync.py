from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data"))).resolve()
DB_PATH = DATA_DIR / "studio.db"
_DONE = False

FORMAT_STRATEGY = """DEFAULT PRODUCTION MODEL — PREMIUM ILLUSTRATED STORYTELLING, NOT FULL ANIMATION.

For Shorts, tell one complete story through approximately 9–12 unique, high-quality 9:16 illustrations over roughly 35–45 seconds. Aim for a fresh visual beat every ~2.5–4 seconds so the viewer continually receives a new image, expression, angle or story development.

Core workflow: source validation → concise story/script → 9–12 cinematic illustrations → Aarav narration → elegant subtitles → restrained ambient music/SFX → clean cuts/subtle dissolves → QA → publish.

Full generative animation is OPTIONAL, not the default. Use it only when physical motion materially improves a scene and the cost/quality is justified. Prefer zero-credit production: static illustrations with very gentle 2–4% camera pushes, parallax/2.5D depth, light/fabric/fire effects and scene changes. Do not rely on Pika/Kling/Pollo-style credit sites to complete every scene.

For selected longer episodes, keep the same illustrated-story identity but allow more scenes and slower pacing."""

VISUAL_STYLE = """Cinematic Indian-epic illustration with textured digital-painting/storybook finish: subtle canvas/paper grain, warm gold/amber light, richly detailed fabrics and architecture, expressive Indian-origin faces, dramatic but respectful composition, shallow cinematic depth and consistent recurring character identities.

Every source image must be a clean standalone vertical 9:16 composition. Never use blurred backing, neighboring-slide bleed, storyboard fragments or visible portions of another scene. Original character designs only; never imitate TV/film costumes, faces or production designs.

Visual motion should remain restrained: gentle camera push/drift, parallax, torch/fire flicker, cloth/hair movement, smoke/dust/light, and small environmental reactions. Avoid face morphing, anatomy mutations, random hand changes, duplicate people or exaggerated motion.

Captions/subtitles should feel ancient and premium rather than modern/generic: classical serif treatment, ivory/gold text, restrained dark maroon/brown or parchment accents when a caption panel is needed. Keep text minimal and highly readable."""

SOURCE_POLICY = """Use reputable primary epic texts and scholarship. Paraphrase rather than copy modern copyrighted translations. Never copy dialogue, music, scenes, costumes, faces or production design from copyrighted TV/film adaptations. Acknowledge textual or interpretive variation when material.

For AI-generated/altered visuals, use YouTube's applicable AI/synthetic-content disclosure when required. AI disclosure is not a reason to avoid AI-assisted illustration; quality, originality, source fidelity and transparency are the priorities."""

CHANNEL_NOTES = """WISDOM OF EPICS — LOCKED CREATIVE PLAYBOOK (09-09-2026)

CREATIVE BENCHMARK / LESSON:
The YouTube channel 'Wisdom of Hope' is a workflow reference only, not a style/copy target. Its videos demonstrate that strong story performance does not require full character animation. The effective pattern is polished textured illustrations + frequent scene turnover + narration + subtitles + music/SFX. The lesson for Wisdom of Epics: art direction, emotional storytelling and pacing matter more than expensive animation.

CHANNEL DIFFERENTIATION:
Wisdom of Epics is specifically about extracting practical modern wisdom from the world's great epics. Each story should end with one clear human lesson in character, judgment, courage, dignity, loyalty, resilience, leadership, ethics or emotional intelligence.

VOICE STANDARD:
NexusTTS → English → India → Aarav – Old Time Storyteller → 1.0x, unless a future test clearly outperforms it.

EDITING / PACING RULES:
- Prefer 9–12 unique story illustrations for a ~35–45 second Short.
- Typical image hold ~3–4 seconds; change sooner where the narration turns.
- Use hard cuts or subtle non-overlapping dissolves; no lingering previous scene.
- Gentle camera motion is optional and should never expose duplicated/blurred neighboring content.
- Add restrained ambience/SFX only where it strengthens immersion: court murmur, cloth movement, conch, wind, fire, footsteps, etc.
- Narration remains primary; music stays underneath and never competes with voice.

QA BEFORE FINAL:
- 1080x1920 final master, true 9:16.
- Inspect mid-scene frames across the entire video.
- No image bleed, black/blurred filler, duplicated scene edges or accidental overlays.
- Character faces/outfits remain consistent.
- Captions readable on a phone.
- ffprobe final resolution, duration and audio stream.

ANIMATION POLICY:
Default = premium illustrated story. Optional enhancement = local/2.5D motion or a small number of AI-generated moving shots. Do not burn free-credit allowances trying to animate every still. Spend AI-video credits only on rare hero moments where natural physical motion adds enough value.

CURRENT VIDEO #3 — DRAUPADI IN THE ROYAL COURT:
Rebuild as a 10–12-scene premium illustrated story rather than a 6-scene animation experiment. Planned visual beats:
1. Hastinapura royal court establishing shot.
2. Draupadi being brought into the court.
3. Draupadi looking across the assembled elders.
4. Draupadi questioning the legality/morality of the wager.
5. Bhishma and senior elders visibly conflicted and silent.
6. Draupadi demanding an answer with dignity and courage.
7. Dushasana reaching for/pulling the loose sari pallu.
8. Draupadi closing her eyes and praying.
9. Endless sari beginning to flow while she remains fully covered.
10. Dushasana straining amid growing folds/piles of cloth.
11. Draupadi standing protected and dignified; court shocked/silent.
12. Reflective closing image emphasizing the cost of powerful people remaining silent during injustice.

TEXTUAL CAUTION FOR VIDEO #3:
Popular/traditional retellings prominently show Krishna protecting Draupadi during the attempted disrobing. Exact treatment varies across Mahabharata textual traditions/redactions, so script wording should avoid claiming one contested physical-detail version as universally identical across all editions unless the chosen source edition is explicitly validated.

Core creative principle: CREATE MORE GREAT FRAMES, NOT MORE EXPENSIVE MOTION."""

MHB003_NOTES = """WISDOM OF EPICS — VIDEO #3 — ACTIVE PRODUCTION.

Topic: Draupadi in the Royal Court
Theme: dignity, injustice, courage, moral accountability, and the danger of powerful people remaining silent when something is clearly wrong.

PRODUCTION DECISION 09-09-2026:
Use the channel's premium illustrated-story format instead of full scene-by-scene AI animation. Target 10–12 unique 9:16 cinematic illustrations over ~35–45 seconds, with Aarav narration, elegant subtitles, restrained ambience/SFX and simple cuts/subtle motion.

PLANNED 12 VISUAL BEATS:
1. Hastinapura royal court establishing shot.
2. Draupadi brought into court.
3. Draupadi surveys the elders.
4. Draupadi challenges the legality/morality of the wager.
5. Senior elders conflicted and silent.
6. Draupadi demands an answer.
7. Dushasana pulls the loose sari pallu.
8. Draupadi prays.
9. Endless sari begins to flow while Draupadi remains fully covered.
10. Dushasana strains amid growing cloth.
11. Draupadi stands protected and dignified; court stunned.
12. Reflective closing frame: silence from the powerful can become part of injustice.

VISUAL CONTINUITY:
Draupadi: consistent Indian-origin face, red/gold royal sari, dignified strength. Court: ornate warm-gold Hastinapura architecture. Correct vastraharan mechanism: Dushasana pulls the loose trailing pallu/end horizontally away from her; cloth continuously extends/unspools while Draupadi remains modestly covered. No skirt-grabbing, tearing, nudity or anatomy distortion.

Source wording must acknowledge textual variation around the exact mechanism of divine intervention unless a specific edition has been chosen and validated."""


def sync_wisdom_epics_playbook() -> None:
    global _DONE
    if _DONE or not DB_PATH.exists():
        return

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "channels" not in tables:
            return

        now = datetime.now().isoformat(timespec="seconds")
        con.execute(
            """UPDATE channels
               SET format_strategy=?, visual_style=?, source_policy=?, notes=?, updated_at=?
               WHERE id=2""",
            (FORMAT_STRATEGY, VISUAL_STYLE, SOURCE_POLICY, CHANNEL_NOTES, now),
        )

        if "ideas" in tables:
            idea = con.execute("SELECT id FROM ideas WHERE idea_id='MHB-003'").fetchone()
            if idea:
                con.execute(
                    """UPDATE ideas
                       SET channel_id=2,
                           pillar='Dignity & Moral Courage',
                           series='Wisdom of Epics — Mahabharata',
                           working_title='Draupadi in the Royal Court',
                           hook='What happens when everyone powerful can see an injustice — and almost no one stops it?',
                           problem='Draupadi confronts humiliation, injustice and the silence of respected elders after the dice game.',
                           safe_action='Dignity includes questioning normalized wrongdoing; people with power also carry responsibility for what they allow through silence.',
                           audience='Global personal-growth and epic-story audience',
                           priority='A+ / VIDEO #3',
                           score=9.9,
                           status='In Production',
                           source_name='Mahabharata — source edition validation required for contested disrobing/intervention details',
                           notes=?
                       WHERE idea_id='MHB-003'""",
                    (MHB003_NOTES,),
                )

        con.commit()
        _DONE = True
    finally:
        con.close()
