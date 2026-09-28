# Alfira: Second Verse

[Русская версия](README.ru.md)

A Baldur's Gate 3 mod that makes Alfira, the tiefling bard of the Emerald Grove, a full companion,
written strictly to the game's canon.

**Status:** 0.8.0, act 1 content complete, being tested in a new playthrough. Acts 2–3 in progress.
Game version: Patch 8 Hotfix 9.

## What's in it

- **Recruitment** after her song in the Grove; party, camp, tent, dismiss and return, level-up.
- **Approval**, 17 reactions to your act 1 choices.
- **Camp chapters 1–8**: long campfire conversations that unlock one per long rest.
- **Talks with a “!” marker** after events and at places (Zevlor's map, the gnolls, the Tollhouse,
  Volo among the goblins and more), plus short scenes before the dialogues of Asharak, Lakrissa and Dammon.
- **Overhead lines** at 41 locations in acts 1–3, on the road, and banter with the party.
- **Romance** with a first kiss; hugs and kisses from the party menu. Open to a hero of any gender.
- **Tiefling celebration** with Alfira as a companion, including a three-way scene with Lakrissa.
- Staging built from her own Larian scenes: facial emotions, poses, seated campfire talks.

## Class

Bard, **College of Lore**. Tiefling (Asmodeus), Entertainer background. She joins at the party's
level. Class, race and tags come from Larian's own unused `Alfira` origin entry, so no stats are overridden.

## Requirements and compatibility

- **No dependencies.** Script Extender is not required (only for the debug commands).
- **Alfira Redux** (appearance): compatible. Load this mod after it.
- **Alfira Joins The Party**: not compatible. Do not enable both.
- **Bhaal's Forgotten Son**: compatible.
- Launch the game with DX11 if Vulkan is unstable on your machine.

## Voice

The public build has no cloned voices. Her original voiced lines from the game play as usual,
and new lines are text only. The author's personal build uses an AI voice clone and is not published
(Larian Fan Content Policy §4.5).

## For developers

Mod sources, scenarios and tools are in this repository. Game data, dialogue dumps and audio are
kept local and are not committed. Plan: [docs/ROADMAP.md](docs/ROADMAP.md).
Workflow rules: [CLAUDE.md](CLAUDE.md).

```bash
cp config/tools.local.example.json config/tools.local.json   # set local paths
python scripts/unpack_game.py goals loca flags dialogs-alfira  # game data → game-data/
python scripts/build_pak.py                                    # → dist/AlfiraSecondVerse.pak
python scripts/install.py                                      # BG3 and BG3 Mod Manager closed
```

Needs Python 3.11+ and [LSLib](https://github.com/Norbyte/lslib). Dialogue staging uses
[bg3moddinglib](https://github.com/0x1amy0urdad/Guidance) (MIT).

## Rights

The project's code and texts belong to the author. Baldur's Gate 3 data, text and audio belong to
Larian Studios and are not included. This is a non-commercial fan mod under the
[Larian Fan Content Policy](https://larian.com/fan-content-policy); see [docs/VOICE.md](docs/VOICE.md).
