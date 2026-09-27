"""Общее для обёрток моделей (запускаются python-ом venv своей модели, не системным).

Протокол: обёртка получает jobs.json (его пишет compare_models.py) и папку вывода.
jobs.json: {"lines": [{id, text, ref_wav, ref_text, instruct, emo_vector, tags}], "variants": N}.
Для каждой реплики и варианта k (1..N) пишет <out>/line<id>_v<k>.wav, в конце — <out>/results.json:
время загрузки, время генерации и длина звука по каждой реплике, пик видеопамяти torch.
"""
import json
import sys
import time
from pathlib import Path


def load_jobs():
    if len(sys.argv) != 3:
        sys.exit("usage: <runner>.py jobs.json out_dir")
    jobs = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    return jobs, out


class Recorder:
    def __init__(self, out, model_name, version):
        import torch
        self.torch = torch
        self.out = out
        self.res = {"model": model_name, "version": version, "items": [], "load_s": None}
        self.t0 = time.perf_counter()
        torch.cuda.reset_peak_memory_stats()

    def loaded(self):
        self.torch.cuda.synchronize()
        self.res["load_s"] = round(time.perf_counter() - self.t0, 1)
        print(f"[{self.res['model']}] загружена за {self.res['load_s']} с", flush=True)

    def item(self, line_id, k, fn, **extra):
        """fn() генерирует и сохраняет файл, возвращает длину звука в секундах."""
        path = self.out / f"line{line_id}_v{k}.wav"
        self.torch.cuda.synchronize()
        t = time.perf_counter()
        try:
            audio_s = fn(path)
            err = ""
        except Exception as e:  # одна неудачная реплика не должна ронять весь прогон
            audio_s, err = 0.0, f"{type(e).__name__}: {e}"
        self.torch.cuda.synchronize()
        gen_s = time.perf_counter() - t
        self.res["items"].append({"id": line_id, "k": k, "file": path.name if not err else "", "gen_s": round(gen_s, 2),
                                  "audio_s": round(audio_s, 2), "error": err, **extra})
        print(f"  line{line_id} v{k}: {gen_s:.1f} с на {audio_s:.1f} с звука {err}", flush=True)

    def save(self):
        t = self.torch.cuda
        self.res["peak_vram_mb"] = round(t.max_memory_reserved() / 2 ** 20)
        self.res["peak_alloc_mb"] = round(t.max_memory_allocated() / 2 ** 20)
        (self.out / "results.json").write_text(json.dumps(self.res, ensure_ascii=False, indent=1), encoding="utf-8")


def save_wav(path, wav, sr):
    import numpy as np
    import soundfile as sf
    a = np.asarray(wav, dtype="float32").reshape(-1)
    sf.write(str(path), a, sr, subtype="PCM_16")
    return len(a) / sr
