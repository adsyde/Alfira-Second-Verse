"""IndexTTS-2.5 (bilibili, github.com/index-tts/index-tts, тег v2.5.0) — обёртка для compare_models.py.

Запуск: voice-work/models/indextts/repo/.venv/Scripts/python.exe, рабочая папка — repo (checkpoints/).
Эмоция: отдельный эмоциональный референс (emo_audio_prompt) или вектор из 8 эмоций.
Варианты:
  v1 — голос и эмоция из одного референса (emo_audio_prompt = тот же файл, emo_alpha 0.8);
  v2 — голос из референса, эмоция вектором из сценария (emo_vector);
  v3 — только референс (эмоцию модель берёт из него сама), другой seed.
У реплики можно задать "custom": {"<k>": {text, ref_wav, emo_ref, emo_alpha, emo_vector, seed}} — переделка.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, ".")
import soundfile as sf  # noqa: E402
import torch  # noqa: E402

from _common import Recorder, load_jobs  # noqa: E402


# Нормализатор IndexTTS раскрывает сокращения («it's» → «it is», «that's» → «that is») — в её речи это
# слышно как чужая подача. Чисел в наших репликах нет, поэтому нормализация выключена.
TEXT_NORM = False


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
        for k in ln.get("variants") or range(1, jobs["variants"] + 1):
            def gen(path, ln=ln, k=k):
                c = (ln.get("custom") or {}).get(str(k))
                if c:   # переделка: свой образец эмоции / вектор / emo_alpha / текст на вариант
                    kw = {}
                    if c.get("emo_ref"):
                        kw.update(emo_audio_prompt=c["emo_ref"], emo_alpha=c.get("emo_alpha", 0.8))
                    if c.get("emo_vector"):
                        kw.update(emo_vector=c["emo_vector"], emo_alpha=c.get("emo_alpha", 1.0))
                    spk, text, seed = c.get("ref_wav", ln["ref_wav"]), c.get("text", ln["text"]), c.get("seed", 1000 + k)
                else:
                    kw, spk, text, seed = settings[k](ln), ln["ref_wav"], ln["text"], 1000 + k
                torch.manual_seed(seed)
                tts.infer(spk_audio_prompt=spk, text=text, output_path=str(path), lang="EN",
                          use_random=False, verbose=False, text_normalization=TEXT_NORM, **kw)
                return sf.info(str(path)).duration
            rec.item(ln["id"], k, gen)
    rec.save()


if __name__ == "__main__":
    main()
