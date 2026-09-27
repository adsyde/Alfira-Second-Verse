"""IndexTTS-2.5 (bilibili, github.com/index-tts/index-tts, тег v2.5.0) — обёртка для compare_models.py.

Запуск: voice-work/models/indextts/repo/.venv/Scripts/python.exe, рабочая папка — repo (checkpoints/).
Эмоция: отдельный эмоциональный референс (emo_audio_prompt) или вектор из 8 эмоций.
Варианты:
  v1 — голос и эмоция из одного референса (emo_audio_prompt = тот же файл, emo_alpha 0.8);
  v2 — голос из референса, эмоция вектором из сценария (emo_vector);
  v3 — только референс (эмоцию модель берёт из него сама), другой seed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, ".")
import soundfile as sf  # noqa: E402
import torch  # noqa: E402

from _common import Recorder, load_jobs  # noqa: E402


def main():
    jobs, out = load_jobs()
    rec = Recorder(out, "indextts", "IndexTTS-2.5 (v2.5.0)")
    from indextts.infer_v2_5 import IndexTTS2
    tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints", use_bf16=True)
    rec.loaded()
    settings = {
        1: lambda ln: {"emo_audio_prompt": ln["ref_wav"], "emo_alpha": 0.8},
        2: lambda ln: {"emo_vector": ln["emo_vector"]},
        3: lambda ln: {},
    }
    for ln in jobs["lines"]:
        for k in range(1, jobs["variants"] + 1):
            def gen(path, ln=ln, k=k):
                torch.manual_seed(1000 + k)
                tts.infer(spk_audio_prompt=ln["ref_wav"], text=ln["text"], output_path=str(path), lang="EN",
                          use_random=False, verbose=False, **settings[k](ln))
                return sf.info(str(path)).duration
            rec.item(ln["id"], k, gen)
    rec.save()


if __name__ == "__main__":
    main()
