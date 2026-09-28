"""Проверка «чей это голос» (venv voice-work/models/_metrics).

  speaker_check.py <items.json> <out.json>

items.json: {"voices": {ключ: [wav её/его чистых реплик игры]}, "items": [{"key", "wav", "speaker"}], "cache"}.
Для каждого файла — косинус эмбеддинга ECAPA (speechbrain/spkrec-ecapa-voxceleb) с центром каждого голоса.
Выход: {"items": [{"key", "speaker", "sims": {голос: косинус}, "nearest"}]}.
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np
import torch
from speechbrain.inference.speaker import EncoderClassifier
from speechbrain.utils.fetching import LocalStrategy

DEV = "cuda" if torch.cuda.is_available() else "cpu"


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    cache = Path(cfg.get("cache", "."))
    enc = EncoderClassifier.from_hparams("speechbrain/spkrec-ecapa-voxceleb", savedir=str(cache / "spkrec-ecapa-voxceleb"),
                                         run_opts={"device": DEV}, local_strategy=LocalStrategy.COPY)

    @torch.no_grad()
    def emb(path):
        y, _ = librosa.load(path, sr=16000, mono=True)
        e = enc.encode_batch(torch.tensor(y)[None].to(DEV)).squeeze().cpu().numpy()
        return e / np.linalg.norm(e)

    centers = {}
    for name, files in cfg["voices"].items():
        c = np.mean([emb(f) for f in files], axis=0)
        centers[name] = c / np.linalg.norm(c)
    out = []
    for i, it in enumerate(cfg["items"]):
        e = emb(it["wav"])
        sims = {n: round(float(e @ c), 4) for n, c in centers.items()}
        out.append({"key": it["key"], "speaker": it["speaker"], "sims": sims, "nearest": max(sims, key=sims.get)})
        if i % 200 == 0:
            print(f"{i}/{len(cfg['items'])}", flush=True)
    Path(sys.argv[2]).write_text(json.dumps({"items": out}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
