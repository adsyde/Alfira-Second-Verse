"""VoxCPM2 (OpenBMB, github.com/OpenBMB/VoxCPM, тег 2.0.3; веса openbmb/VoxCPM2) — обёртка для compare_models.py.

Запуск: voice-work/models/voxcpm/.venv/Scripts/python.exe, рабочая папка — voice-work/models/voxcpm (weights/).
Эмоция: «ultimate cloning» (референс + его текст — модель продолжает его подачу) или описание стиля
в скобках в начале текста: "(tipsy, giggly)Text".
Варианты:
  v1 — ultimate cloning: prompt_wav + prompt_text + reference_wav = референс эмоции;
  v2 — reference_wav + стиль из сценария в скобках;
  v3 — ultimate cloning, cfg 2.5, другой seed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import torch  # noqa: E402

from _common import Recorder, load_jobs, save_wav  # noqa: E402


def main():
    jobs, out = load_jobs()
    rec = Recorder(out, "voxcpm", "VoxCPM2 (voxcpm 2.0.3)")
    from voxcpm import VoxCPM
    m = VoxCPM.from_pretrained("weights", load_denoiser=False, optimize=False)
    sr = m.tts_model.sample_rate
    rec.loaded()
    for ln in jobs["lines"]:
        ult = {"prompt_wav_path": ln["ref_wav"], "prompt_text": ln["ref_text"], "reference_wav_path": ln["ref_wav"]}
        settings = {
            1: (ln["text"], {**ult, "cfg_value": 2.0}),
            2: (f"({ln['instruct']}){ln['text']}", {"reference_wav_path": ln["ref_wav"], "cfg_value": 2.0}),
            3: (ln["text"], {**ult, "cfg_value": 2.5}),
        }
        for k in range(1, jobs["variants"] + 1):
            def gen(path, k=k):
                torch.manual_seed(2000 + k)
                text, kw = settings[k]
                wav = m.generate(text=text, inference_timesteps=10, **kw)
                return save_wav(path, wav, sr)
            rec.item(ln["id"], k, gen)
    rec.save()


if __name__ == "__main__":
    main()
