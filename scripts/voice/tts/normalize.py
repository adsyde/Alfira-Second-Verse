"""Приводит варианты к одному виду для слепого прослушивания (venv _metrics).

  normalize.py <pairs.json>     # [[src, dst], ...]

48 кГц, моно, 16 бит; громкость по RMS речи к −20 дБFS с ограничением пика −1 дБFS;
тишина по краям подрезается до 0,15 с. Так частота дискретизации и уровень не выдают модель.
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

SR = 48000
TARGET_RMS_DB = -20.0
PEAK_DB = -1.0


def main():
    for src, dst in json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")):
        y, _ = librosa.load(src, sr=SR, mono=True, res_type="soxr_hq")
        yt, (a, b) = librosa.effects.trim(y, top_db=45)
        pad = int(0.15 * SR)
        y = y[max(0, a - pad): min(len(y), b + pad)]
        voiced = np.abs(y) > 10 ** (-45 / 20)
        rms = np.sqrt(np.mean(y[voiced] ** 2)) if voiced.any() else 1e-4
        y = y * (10 ** (TARGET_RMS_DB / 20) / rms)
        peak = np.abs(y).max()
        if peak > 10 ** (PEAK_DB / 20):
            y = y * (10 ** (PEAK_DB / 20) / peak)
        sf.write(dst, y.astype("float32"), SR, subtype="PCM_16")


if __name__ == "__main__":
    main()
