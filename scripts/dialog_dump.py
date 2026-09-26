#!/usr/bin/env python3
"""Превращает диалог игры (.lsj) в читаемый сценарий.

Печатает дерево узлов: кто говорит, реплика EN и RU, проверки и установки
флагов, броски, контекст для постановщика. Повторно встреченные узлы
обозначаются ссылкой «↩ N123», чтобы циклы не разворачивались бесконечно.

  python scripts/dialog_dump.py DEN_TieflingBard_Bard            # по имени файла
  python scripts/dialog_dump.py path/to/file.lsj --out reports/x.md
  python scripts/dialog_dump.py --all-alfira                       # все, где говорит Альфира → reports/dialogs/
"""
import argparse
import json
import sys

from common import enable_utf8_stdout, game_data_dir, resolve
from gamedb import ALFIRA, name, text

enable_utf8_stdout()


def val(node, key, default=""):
    v = node.get(key)
    return v.get("value", default) if isinstance(v, dict) else default


def editor(node):
    out = {}
    for block in node.get("editorData", []):
        for d in block.get("data", []):
            out[d["key"]["value"]] = d["val"]["value"]
    return out


def flags(node, key):
    res = []
    for block in node.get(key, []):
        for group in block.get("flaggroup", []):
            kind = group["type"]["value"]
            for f in group.get("flag", []):
                guid = f["UUID"]["value"]
                on = f["value"]["value"]
                res.append(f"{'' if on else '!'}{name(guid)} [{kind}]")
    return res


def lines(node):
    res = []
    for tt in node.get("TaggedTexts", []):
        for t in tt.get("TaggedText", []):
            for texts in t.get("TagTexts", []):
                for x in texts.get("TagText", []):
                    h = x["TagText"]["handle"]
                    res.append((h, text(h, "en"), text(h, "ru")))
    return res


def load(path):
    d = json.loads(path.read_text(encoding="utf-8"))["save"]["regions"]
    dlg = d["dialog"]
    speakers = {}
    for sl in dlg.get("speakerlist", []):
        for s in sl.get("speaker", []):
            guids = [g for g in s["list"]["value"].split(";") if g]
            speakers[int(s["index"]["value"])] = ", ".join(name(g) for g in guids) or "?"
    nodes = {n["UUID"]["value"]: n for n in dlg["nodes"][0].get("node", [])}
    roots = [r["RootNodes"]["value"] for r in dlg["nodes"][0].get("RootNodes", [])]
    synopsis = val(d.get("editorData", {}), "synopsis")
    return speakers, nodes, roots, synopsis


def render(path):
    speakers, nodes, roots, synopsis = load(path)
    out = [f"# {path.stem}", ""]
    if synopsis:
        out += ["> " + synopsis.replace("\r", "").replace("\n", "\n> "), ""]
    out += ["Участники: " + "; ".join(f"{i}={s}" for i, s in sorted(speakers.items())), ""]
    ids = {u: editor(n).get("ID", u[:6]) for u, n in nodes.items()}
    seen = set()

    def walk(uid, depth):
        n = nodes.get(uid)
        pad = "  " * depth
        if n is None:
            return
        if uid in seen:
            out.append(f"{pad}↩ {ids[uid]}")
            return
        seen.add(uid)
        kind = val(n, "constructor")
        ed = editor(n)
        spk = n.get("speaker", {}).get("value", -1)
        # У Larian TagQuestion — выбор игрока, TagAnswer/TagGreeting — реплика NPC
        who = "Игрок" if kind == "TagQuestion" else speakers.get(spk, "Рассказчик" if spk == -666 else "")
        head = f"{pad}- {ids[uid]} {kind}"
        if kind == "ActiveRoll" or kind == "PassiveRoll":
            head += f" [{val(n, 'Ability')}/{val(n, 'Skill')}]"
        if kind == "RollResult":
            head += " успех" if val(n, "Success") else " провал"
        if kind == "Jump":
            head += f" → {ids.get(val(n, 'jumptarget'), '?')}"
        out.append(head)
        for h, en, ru in lines(n):
            out.append(f"{pad}  **{who}**: {en or '(нет текста) ' + h}")
            if ru:
                out.append(f"{pad}  _{ru}_")
        ctx = ed.get("CinematicNodeContext") or ed.get("stateContext") or ed.get("NodeContext")
        if ctx:
            out.append(f"{pad}  «{ctx.strip()}»")
        for label, key in (("если", "checkflags"), ("ставит", "setflags")):
            f = flags(n, key)
            if f:
                out.append(f"{pad}  {label}: " + ", ".join(f))
        for c in n.get("children", [{}])[0].get("child", []):
            walk(c["UUID"]["value"], depth + 1)

    for r in roots:
        walk(r, 0)
        out.append("")
    return "\n".join(out)


def find(stem):
    hits = [p for p in game_data_dir().rglob(f"{stem}.lsj")]
    if not hits:
        sys.exit(f"Не найден {stem}.lsj в game-data (распакуйте нужный набор unpack_game.py)")
    return hits[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dialog", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--all-alfira", action="store_true")
    args = ap.parse_args()

    if args.all_alfira:
        dest = resolve("reports/dialogs")
        dest.mkdir(parents=True, exist_ok=True)
        n = 0
        for p in sorted(game_data_dir().rglob("*.lsj")):
            if "Story/Dialogs" not in p.as_posix() or ALFIRA not in p.read_text(encoding="utf-8"):
                continue
            (dest / f"{p.stem}.md").write_text(render(p), encoding="utf-8")
            n += 1
        print(f"{n} диалогов → {dest}")
        return

    p = resolve(args.dialog) if args.dialog.endswith(".lsj") else find(args.dialog)
    md = render(p)
    if args.out:
        resolve(args.out).write_text(md, encoding="utf-8")
    else:
        print(md)


if __name__ == "__main__":
    main()
