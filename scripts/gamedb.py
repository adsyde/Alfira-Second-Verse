"""Справочники по распакованным данным игры: тексты (loca EN/RU) и имена GUID.

Кэш кладётся в game-data/_cache.pkl и пересобирается, если его нет.
Нужны наборы unpack: loca, goals и flags (имена флагов и тегов).
"""
import html
import pickle
import re

from common import game_data_dir

LOCA_RE = re.compile(r'<content contentuid="([^"]+)"[^>]*>(.*?)</content>', re.S)
# В Osiris-скриптах объекты и флаги пишутся как Имя_<guid>
NAMED_GUID_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*?)_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b")

FLAG_RE = re.compile(r'id="Name" type="FixedString" value="([^"]*)".*?id="UUID" type="guid" value="([^"]*)"', re.S)

ALFIRA = "4a405fba-3000-4c63-97e5-a8001ebb883c"  # S_DEN_Bard, глобальный персонаж всех трёх актов

_db = None


def _load_loca(folder):
    texts = {}
    # Основной файл языка последним: у него приоритет над вариантами по полу (_to_F и т. п.)
    files = sorted(folder.rglob("*.xml"), key=lambda p: p.stem.lower() in ("english", "russian"))
    for f in files:
        for uid, text in LOCA_RE.findall(f.read_text(encoding="utf-8", errors="replace")):
            texts[uid] = html.unescape(text)
    return texts


def _build():
    root = game_data_dir()
    names = {}
    # Имена флагов и тегов из их определений (Public/*/Flags|Tags/*.lsx) — самые точные
    for kind in ("Flags", "Tags"):
        for f in root.glob(f"*/Public/*/{kind}/*.lsx"):
            m = FLAG_RE.search(f.read_text(encoding="utf-8", errors="replace"))
            if m:
                names[m.group(2)] = m.group(1)
    for f in root.rglob("Goals/*.txt"):
        for name, guid in NAMED_GUID_RE.findall(f.read_text(encoding="utf-8", errors="replace")):
            names.setdefault(guid, name)
    return {
        "en": _load_loca(root / "Localization_English"),
        "ru": _load_loca(root / "Localization_Russian_Russian"),
        "names": names,
    }


def db(rebuild=False):
    global _db
    if _db is None:
        cache = game_data_dir() / "_cache.pkl"
        if cache.exists() and not rebuild:
            _db = pickle.loads(cache.read_bytes())
        else:
            _db = _build()
            cache.write_bytes(pickle.dumps(_db))
    return _db


def text(handle, lang="en"):
    return db()[lang].get(handle, "")


def name(guid):
    if guid == ALFIRA:
        return "ALFIRA"
    return db()["names"].get(guid, guid[:8])
