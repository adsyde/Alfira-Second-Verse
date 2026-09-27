"""Chatterbox (Resemble AI, github.com/resemble-ai/chatterbox, pip chatterbox-tts 0.1.7) — обёртка для compare_models.py.

Запуск: voice-work/models/chatterbox/.venv/Scripts/python.exe. Веса ResembleAI/chatterbox — в HF_HOME.
Эмоция: референс задаёт и тембр, и подачу; ручка exaggeration усиливает выразительность,
cfg_weight — темп (ниже — медленнее и выразительнее). В звук встроен неслышимый водяной знак Perth.
Варианты: v1 exaggeration 0.5 / cfg 0.5 (по умолчанию); v2 0.7 / 0.3; v3 0.9 / 0.3.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import torch  # noqa: E402

from _common import Recorder, load_jobs, save_wav  # noqa: E402


def main():
    jobs, out = load_jobs()
    rec = Recorder(out, "chatterbox", "Chatterbox 0.1.7 (English)")
    from chatterbox.tts import ChatterboxTTS
    m = ChatterboxTTS.from_pretrained(device="cuda")
    rec.loaded()
    settings = {1: (0.5, 0.5), 2: (0.7, 0.3), 3: (0.9, 0.3)}
    for ln in jobs["lines"]:
        for k in range(1, jobs["variants"] + 1):
            def gen(path, k=k):
                torch.manual_seed(3000 + k)
                ex, cfg = settings[k]
                wav = m.generate(ln["text"], audio_prompt_path=ln["ref_wav"], exaggeration=ex, cfg_weight=cfg)
                return save_wav(path, wav.squeeze(0).cpu().numpy(), m.sr)
            rec.item(ln["id"], k, gen)
    rec.save()


if __name__ == "__main__":
    main()
