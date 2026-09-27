"""Объективные метрики сравнения (запускается python-ом venv voice-work/models/_metrics).

  metrics.py <items.json> <out.json>

items.json: {"voice_set": [wav её голоса для «центра»], "items": [{"key", "wav", "text", "ref"}]}.
Для каждого файла:
  - sim_ecapa — косинус эмбеддинга ECAPA (speechbrain/spkrec-ecapa-voxceleb) с центром её голоса
    (среднее по voice_set), sim_ecapa_ref — с референсом, который получила модель;
  - sim_wavlm — то же для WavLM-SV (microsoft/wavlm-base-plus-sv);
  - sim_*_target — с её настоящей репликой того же текста (набор «тот же текст», если задан target);
  - wer — ошибка распознавания Whisper (large-v3-turbo) против текста реплики, после нормализации.
"""
import json
import re
import sys
from pathlib import Path

import jiwer
import librosa
import numpy as np
import torch
import whisper
from speechbrain.inference.speaker import EncoderClassifier
from transformers import AutoFeatureExtractor, WavLMForXVector

DEV = "cuda" if torch.cuda.is_available() else "cpu"


def load16(path):
    y, _ = librosa.load(path, sr=16000, mono=True)
    return y


def norm(s):
    s = re.sub(r"<[^>]+>", "", s.lower().replace("’", "'"))
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    items = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    cache = Path(items.get("cache", "."))

    from speechbrain.utils.fetching import LocalStrategy   # без симлинков: на Windows они требуют прав
    ecapa = EncoderClassifier.from_hparams("speechbrain/spkrec-ecapa-voxceleb", savedir=str(cache / "spkrec-ecapa-voxceleb"),
                                           run_opts={"device": DEV}, local_strategy=LocalStrategy.COPY)
    fe = AutoFeatureExtractor.from_pretrained("microsoft/wavlm-base-plus-sv")
    wavlm = WavLMForXVector.from_pretrained("microsoft/wavlm-base-plus-sv").to(DEV).eval()

    @torch.no_grad()
    def emb(path):
        y = load16(path)
        e1 = ecapa.encode_batch(torch.tensor(y)[None].to(DEV)).squeeze().cpu().numpy()
        inp = fe(y, sampling_rate=16000, return_tensors="pt").to(DEV)
        e2 = wavlm(**inp).embeddings.squeeze().cpu().numpy()
        return e1 / np.linalg.norm(e1), e2 / np.linalg.norm(e2)

    cache_emb = {}

    def get(path):
        if path not in cache_emb:
            cache_emb[path] = emb(path)
        return cache_emb[path]

    vs = [get(p) for p in items["voice_set"]]
    c1 = np.mean([a for a, _ in vs], axis=0)
    c2 = np.mean([b for _, b in vs], axis=0)
    c1, c2 = c1 / np.linalg.norm(c1), c2 / np.linalg.norm(c2)
    # разброс её собственных реплик относительно центра — «потолок» похожести
    self_sim = {"ecapa": float(np.mean([a @ c1 for a, _ in vs])), "wavlm": float(np.mean([b @ c2 for _, b in vs]))}

    asr = whisper.load_model("turbo", device=DEV, download_root=str(cache / "whisper"))
    res = []
    for it in items["items"]:
        e1, e2 = get(it["wav"])
        r = {"key": it["key"], "sim_ecapa": float(e1 @ c1), "sim_wavlm": float(e2 @ c2)}
        if it.get("ref"):
            r1, r2 = get(it["ref"])
            r["sim_ecapa_ref"] = float(e1 @ r1)
            r["sim_wavlm_ref"] = float(e2 @ r2)
        if it.get("target"):   # «тот же текст»: её настоящая реплика с этим текстом
            t1, t2 = get(it["target"])
            r["sim_ecapa_target"] = float(e1 @ t1)
            r["sim_wavlm_target"] = float(e2 @ t2)
        hyp = asr.transcribe(load16(it["wav"]), language="en", fp16=DEV == "cuda")["text"]   # массив: без ffmpeg
        r["asr"] = hyp.strip()
        r["wer"] = float(jiwer.wer(norm(it["text"]), norm(hyp) or "-"))
        res.append(r)
        print(f"{it['key']}: ecapa {r['sim_ecapa']:.3f} wavlm {r['sim_wavlm']:.3f} wer {r['wer']:.2f}", flush=True)
    out.write_text(json.dumps({"self_sim": self_sim, "items": res}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
