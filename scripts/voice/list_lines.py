#!/usr/bin/env python3
"""Список новых реплик Альфиры (✍️) акта 1 для озвучки клоном: handle, текст, эмоция.

Источник — сцены scripts/dialogs/scenes/*.py (то же, из чего собирается мод): главы 1–8,
разговор в отряде (поцелуи и объятия), вербовка, реакции и места акта 1, фразы в пути,
беседы отряда. Берутся её текстовые реплики say(): не voice() (голос игры), не narrate()
и не реплики третьего участника сцены. Handle — из loca мода
(mod/Mods/_MOD_/Localization/English/AlfiraSecondVerse_en.xml) по тексту; у одинакового текста
в разных сценах несколько handle — звук один.

Эмоция реплики (папка voice-work/refs/<эмоция>/) выводится из сценария:
  1) ремарка note («(смеётся)», «(тихо)», «(краснеет)»…) — NOTE_RULES;
  2) контекст сцены: праздник — навеселе, «Утро после» — похмелье, поцелуи — флирт (SCENE_RULES);
  3) эмоции лица emo ("sad>fear/1"): преобладающая — FACE_CAT.
К эмоции — инструкция подачи для Breeze (по-английски) и вектор IndexTTS.

  python scripts/voice/list_lines.py          # → voice-work/act1/lines.json и сводка
"""
import dataclasses
import html
import importlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "dialogs"))
from common import ROOT, config, enable_utf8_stdout, resolve  # noqa: E402

enable_utf8_stdout()
import dsl  # noqa: E402

# (модуль сцены, группа на странице прослушивания) — порядок = порядок прослушивания
GROUPS = [
    ("ch01_first_night", "Глава 1. Первая ночь в дороге"),
    ("ch02_lute", "Глава 2. Лютня"),
    ("recruitment", "Вербовка"),
    ("ch03_first_verse", "Глава 3. Первый куплет"),
    ("ch04_celebration", "Глава 4. Праздник"),
    ("ch05_morning_after", "Глава 5. Утро после"),
    ("ch06_elturel", "Глава 6. Элтуриэль"),
    ("ch07_fear", "Глава 7. Страх"),
    ("ch08_first_kiss", "Глава 8. Первый поцелуй"),
    ("inparty", "Разговор в отряде: поцелуи и объятия"),
    ("places", "Реакции и места акта 1"),
    ("travel", "Фразы в пути"),
    ("banter", "Беседы отряда"),
]

# ремарка сценария → эмоция (первое совпадение)
NOTE_RULES = [
    (r"сквозь слёзы|плач", "tearful"),
    (r"смеёт|хохоч|давится смехом|фыркает|смех", "laugh"),
    (r"шёпот|тихо|тише|вполголоса", "whisper"),
    (r"красне|смущ|прячет лицо", "embarrassed"),
    (r"сияет|восторг", "excited"),
    (r"подмиг|прищур|не верит ни слову", "teasing"),
    (r"прохладно|резко|обиженно|холодн", "angry"),
    (r"напевает", "neutral"),
]
FACE_CAT = {"happy": "grateful", "angry": "angry", "sad": "sad", "fear": "fear", "surprise": "surprise",
            "disgust": "angry", "pain": "sad", "thinking": "neutral", "confusion": "neutral", "neutral": "neutral"}
# подача по эмоции: инструкция Breeze и вектор IndexTTS [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]
STYLE = {
    "neutral": ("natural, conversational, warm young woman", [0, 0, 0, 0, 0, 0, 0, 0.8]),
    "grateful": ("warm and friendly, gently smiling", [0.5, 0, 0, 0, 0, 0, 0, 0.5]),
    "laugh": ("laughing, amused, playful", [0.8, 0, 0, 0, 0, 0, 0.1, 0.1]),
    "embarrassed": ("flustered and embarrassed, shy, a nervous little laugh", [0.3, 0, 0, 0.3, 0, 0, 0.3, 0.1]),
    "flirty": ("flirty, playful and affectionate, smiling, intimate", [0.6, 0, 0, 0, 0, 0, 0.1, 0.3]),
    "tearful": ("emotional, voice breaking, laughing through tears", [0.3, 0, 0.5, 0, 0, 0.2, 0, 0]),
    "teasing": ("teasing, dry and playful, a smile in the voice", [0.5, 0, 0, 0, 0, 0, 0.1, 0.4]),
    "angry": ("hurt and irritated, sharp, bitter", [0, 0.6, 0.3, 0, 0, 0, 0, 0.1]),
    "fear": ("scared, shaky voice, anxious", [0, 0, 0.2, 0.7, 0, 0, 0, 0.1]),
    "sad": ("quiet, sad, grieving", [0, 0, 0.6, 0, 0, 0.4, 0, 0]),
    "tired": ("tired and worn out, low energy", [0, 0, 0.2, 0, 0, 0.4, 0, 0.4]),
    "excited": ("beaming, excited and delighted", [0.8, 0, 0, 0, 0, 0, 0.2, 0]),
    "surprise": ("surprised, caught off guard", [0.2, 0, 0, 0.1, 0, 0, 0.6, 0.1]),
    "whisper": ("quiet, almost whispering, soft and intimate", [0, 0, 0.3, 0, 0, 0.3, 0, 0.4]),
    "drunk": ("tipsy, a bit drunk, giggly and sentimental, slightly slurred", [0.7, 0, 0, 0, 0, 0, 0.2, 0.1]),
    # похмелья в её записях нет: образец «усталость», подача — инструкцией
    "hungover": ("hungover and groggy, tired, dry self-deprecating humour", [0.1, 0, 0.2, 0, 0, 0.3, 0, 0.4]),
}
REF_OF = {"hungover": "tired"}           # эмоция → папка refs, если своей нет
VECTOR_EXTRA = {"laugh", "flirty", "excited"}   # IndexTTS: 3 варианта вместо 2


def walk(o, block, seen, out):
    if id(o) in seen:
        return
    seen.add(id(o))
    if isinstance(o, dsl.Line):
        out.append((o, block))
        return
    if isinstance(o, dsl.Block):
        block = o.id
    if dataclasses.is_dataclass(o) and not isinstance(o, type):
        for f in dataclasses.fields(o):
            walk(getattr(o, f.name), block, seen, out)
    elif isinstance(o, (list, tuple, set)):
        for x in o:
            walk(x, block, seen, out)
    elif isinstance(o, dict):
        for x in o.values():
            walk(x, block, seen, out)


def module_lines(name):
    mod = importlib.import_module(f"scenes.{name}")
    out, seen = [], set()
    roots = [v for k, v in vars(mod).items() if not k.startswith("_")]
    if name == "places":
        roots = [p for p in mod.PLACES if p.act == 1]     # места актов 2–3 — позже
    for v in roots:
        walk(v, "", seen, out)
    return out


def dominant_face(emo):
    toks = [t for _, t in emo] if isinstance(emo, list) else emo.split(">")
    names = [t.strip().partition("/")[0] for t in toks]
    c = Counter(n for n in names if n not in ("neutral", "thinking", "confusion"))
    return c.most_common(1)[0][0] if c else names[0]


def category(line, group, block):
    for rx, cat in NOTE_RULES:
        if line.note and re.search(rx, line.note, re.I):
            return cat, f"ремарка «{line.note}»"
    face = FACE_CAT.get(dominant_face(line.emo), "neutral")
    if group == "ch04_celebration" and face in ("grateful", "neutral", "surprise", "excited", "teasing"):
        return "drunk", "праздник"
    # «Утро после»: похмелье — только где оно слышно (боль на лице, вино, вода), разговор о романе — по лицу
    hang = "pain" in str(line.emo) or re.search(r"wine|hungover|water|loudly|drunk", line.en, re.I)
    if group == "ch05_morning_after" and hang and face in ("neutral", "sad", "grateful"):
        return "hungover", "утро после праздника"
    if (group == "ch08_first_kiss" or re.search(r"kiss|hug", block, re.I)) and face in ("grateful", "neutral"):
        return "flirty", "поцелуи и объятия"
    return face, f"лицо {line.emo}"


def loca_handles():
    p = ROOT / "mod" / "Mods" / "_MOD_" / "Localization" / "English" / "AlfiraSecondVerse_en.xml"
    by = {}
    for h, t in re.findall(r'<content contentuid="([^"]+)"[^>]*>(.*?)</content>', p.read_text(encoding="utf-8"), re.S):
        by.setdefault(html.unescape(t), []).append(h)
    return by


def main():
    vw = resolve(config()["paths"]["voice_work"])
    loca = loca_handles()
    lines, seen_text, missing = [], {}, []
    for group, title in GROUPS:
        for ln, block in module_lines(group):
            if not ln.en or ln.handle or ln.narrator or ln.speaker != dsl.ALFIRA:
                continue
            en = dsl.render(ln.en)
            if en in seen_text:
                continue
            handles = loca.get(en)
            if not handles:
                missing.append(f"{group}: {en[:60]}")
                continue
            cat, why = category(ln, group, block)
            instr, vec = STYLE[cat]
            item = {"id": handles[0], "handles": handles, "group": group, "group_title": title, "block": block,
                    "en": en, "text": re.sub(r"<[^>]+>", "", en), "ru": dsl.render(ln.ru),
                    "emo": ln.emo if isinstance(ln.emo, str) else json.dumps(ln.emo), "note": ln.note,
                    "emotion": cat, "why": why, "ref_emotion": REF_OF.get(cat, cat), "instruct": instr,
                    "emo_vector": vec, "tags": "laugh" if cat == "laugh" else "",
                    "index_variants": 3 if cat in VECTOR_EXTRA else 2}
            seen_text[en] = item
            lines.append(item)
    out = vw / "act1" / "lines.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(lines, ensure_ascii=False, indent=1), encoding="utf-8")
    words = sum(len(x["text"].split()) for x in lines)
    print(f"реплик: {len(lines)} (handle: {sum(len(x['handles']) for x in lines)}), слов {words}, "
          f"≈ {words / 2.6 / 60:.0f} мин звука")
    print("по группам:", dict(Counter(x["group"] for x in lines)))
    print("по эмоциям:", dict(Counter(x["emotion"] for x in lines)))
    if missing:
        print(f"не найдено в loca мода ({len(missing)}):\n  " + "\n  ".join(missing))
    print(f"→ {out}")


if __name__ == "__main__":
    main()
