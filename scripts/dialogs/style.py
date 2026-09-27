"""Её собственная постановка лица и тела в текстовых репликах — по словарю alfira_style.json.

Словарь строит scripts/dialogs/alfira_catalog.py из её реплик у Larian (548 реплик, 34 диалога): для каждой
эмоции — какие вариации она играет и как часто меняется ключ, для каждой ремарки сценария — какие лица у неё
в репликах с такой же ремаркой редактора Larian. Сводка — docs/research/alfira-staging.md.

Вариация эмоции у Larian — это не только лицо. В Public/Shared/Animation/Emotions.lsf (AnimSetToShortNames)
у каждой эмоции по 6 анимаций-вариантов, и номер вариации ключа TLEmotionEvent выбирает, какая из них играет:
жест, наклон головы, плечи. Отдельные TLAnimation в её репликах почти не встречаются (12 на 548, только в
DEN_TieflingBard_Bard), поэтому её «жесты» переносятся вариациями эмоций.

Формат сцен не меняется (scripts/dialogs/README.md):
  * emo="happy" — эмоция без вариации: её вариации, по ключу на 2–4 с, как в её репликах;
  * emo="happy/2" или список [(0.0, "fear"), …] — ровно как написано (решение автора сцены);
  * note="(краснеет)" или текст ремарки рассказчика («She laughs…») — вариации берутся из её реплик с такой
    ремаркой у Larian; если emo не задана (neutral), лицо — её главное лицо для этой ремарки.
ENABLED = False возвращает прежний шаблон: один ключ с вариацией 0 на каждую эмоцию.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from dsl import EMOTIONS, emotion_keys

STYLE_FILE = Path(__file__).with_name("alfira_style.json")
ENABLED = True
MAX_VARIATION = 5          # у эмоции в Emotions.lsf 6 вариантов (0–5); 23, 24 и т. п. — особые, их не берём
TOP = 3                    # сколько её вариаций на эмоцию чередовать
MIN_STEP, MAX_STEP = 2.0, 4.0   # секунд на ключ (у неё в среднем ключ каждые ~2 с)

# Ремарки сценария по-русски (note=…, design/dialogs/*.md) → ключ ремарки словаря (alfira_catalog.REMARKS).
RU_STEMS = {
    "краснеет": ("красне", "смущ", "покрасн"),
    "смеётся": ("смеёт", "смеет", "смех", "смеш", "хихик"),
    "улыбается": ("улыб",),
    "плачет": ("плач", "слёз", "слез", "всхлип", "рыда"),
    "грустно": ("грус", "печал", "тоск", "гаснет"),
    "тихо": ("тихо", "тише", "шёпот", "шепч", "шёпотом"),
    "испуг": ("страх", "испуг", "нервн", "боит", "дрож"),
    "злится": ("злит", "злая", "злой", "сердит", "раздраж", "обиж"),
    "думает": ("дума", "задумч", "размышл"),
    "удивлена": ("удивл", "замира", "ошеломл"),
    "нежно": ("нежн", "ласк", "тепло"),
    "дразнит": ("дразн", "подмиг", "лукав", "игрив"),
    "гордо": ("горд",),
    "восторг": ("восторг", "радост", "сияет"),
    "устала": ("устал", "зева", "сонн", "засыпа"),
    "пожимает плечами": ("пожима",),
    "вздыхает": ("вздых", "вздох"),
    "пьяная": ("пьян",),
    "поёт": ("поёт", "напева"),
    "играет на лютне": ("лютн",),
}


class Style:
    def __init__(self, path: Path = STYLE_FILE):
        self.data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    # --- ремарка ---

    def remark(self, line) -> str:
        """Ключ ремарки словаря по note (по-русски) и по тексту ремарки рассказчика (по-английски)."""
        if not self.data:
            return ""
        rems = self.data.get("remarks", {})
        note = (line.note or "").lower()
        for key, stems in RU_STEMS.items():
            if key in rems and any(s in note for s in stems):
                return key
        en = " ".join(((line.en or "") if line.narrator else "", note)).lower()
        for key, r in rems.items():
            if any(re.search(r"\b" + re.escape(w), en) for w in r.get("words", [])):
                return key
        return ""

    # --- вариации ---

    def variations(self, emo: str, remark: str = "") -> list[int]:
        """Её вариации эмоции по частоте: сперва в репликах с этой ремаркой, иначе во всех её репликах."""
        out = []
        if remark:
            for tok, _ in self.data["remarks"][remark]["faces"]:
                name, _, var = tok.partition("/")
                if name == emo and int(var) <= MAX_VARIATION and int(var) not in out:
                    out.append(int(var))
        if not out:
            out = [int(v) for v, _ in self.data["emotions"].get(emo, {}).get("variations", []) if int(v) <= MAX_VARIATION]
        return out[:TOP]

    def step(self, emo: str) -> float:
        kps = self.data["emotions"].get(emo, {}).get("keys_per_second", 0) or 0
        return min(MAX_STEP, max(MIN_STEP, 1 / kps)) if kps else MAX_STEP

    def keys(self, line, duration: float, seed: str) -> list[tuple[float, int, int]]:
        """[(секунда от начала фазы, код эмоции, вариация)] для лица Альфиры в текстовой реплике или ремарке."""
        emo = line.emo
        if not ENABLED or not self.data or not isinstance(emo, str):
            return emotion_keys(emo, duration)
        remark = self.remark(line)
        if emo == "neutral" and remark:
            # эмоция не задана, а ремарка есть — её главное лицо для этой ремарки у Larian
            top = self.data["remarks"][remark]["dominant"]
            if top:
                emo = top[0][0]
        toks = emo.split(">")
        h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
        out = []
        for i, tok in enumerate(toks):
            name, _, var = tok.strip().partition("/")
            if name not in EMOTIONS:
                raise ValueError(f"неизвестная эмоция {name!r}; есть {sorted(EMOTIONS)}")
            t0, seg = duration * i / len(toks), duration / len(toks)
            if var != "":
                out.append((round(t0, 2), EMOTIONS[name], int(var)))
                continue
            vs = self.variations(name, remark) or [0]
            n = max(1, int(seg // self.step(name)))
            first = (h >> (4 * i)) % len(vs)
            for j in range(n):
                v = vs[(first + j) % len(vs)]
                if out and out[-1][1:] == (EMOTIONS[name], v):
                    continue
                out.append((round(t0 + j * seg / n, 2), EMOTIONS[name], v))
        return out


STYLE = Style()
