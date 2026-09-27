"""Breeze TTS 2 (BreezeBlue, github.com/breezeblue-ai/breeze-tts; веса BreezeBlue/Breeze-TTS-2) — обёртка для
compare_models.py. Повторяет infer.py репозитория, но грузит модель один раз на все реплики.

Запуск: voice-work/models/breeze/.venv/Scripts/python.exe, рабочая папка — repo; веса — ../weights.
Эмоция: «Voice Direction» — референс + его текст + свободная инструкция (cfg 4), звуки в тексте:
(laugh), (sigh), (cough). Без инструкции — обычный клон (подача из референса).
Варианты: v1 — клон без инструкции (cfg 1); v2 — инструкция из сценария (cfg 4);
v3 — инструкция + звук из сценария в тексте (cfg 3), другой seed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, ".")
import soundfile as sf  # noqa: E402

from _common import Recorder, load_jobs  # noqa: E402

MAX_NEW_TOKENS, MAX_SEQ_LEN, REPETITION_PENALTY = 1500, 2048, 1.1


def main():
    jobs, out = load_jobs()
    rec = Recorder(out, "breeze", "Breeze TTS 2 (код 008f769)")
    from breeze_infer.runtime import load_runtime, resolve_device, set_all_seeds, update_generation_config_for_breeze
    from breeze_infer.templates import get_template, prepare_inputs, select_template_name
    from models.fast_streaming import FastBreezeStreamingRuntime, FastStreamingConfig
    tokenizer, model, audio_tokenizer = load_runtime(Path("../weights"), device=resolve_device(),
                                                     attn_implementation="eager")
    update_generation_config_for_breeze(model)
    cfg = FastStreamingConfig(max_new_tokens=MAX_NEW_TOKENS, max_seq_len=MAX_SEQ_LEN, fast_all=False,
                              fast_text_encoder=False, fast_backbone_prefill=False, fast_backbone_decode=False,
                              fast_depth_decoder=False, fast_codec=False, repetition_penalty=REPETITION_PENALTY)
    runtime = FastBreezeStreamingRuntime(model, audio_tokenizer, cfg, tokenizer=tokenizer)
    rec.loaded()
    for ln in jobs["lines"]:
        tagged = f"({ln['tags']}) {ln['text']}" if ln.get("tags") else ln["text"]
        settings = {1: (ln["text"], None, 1.0), 2: (ln["text"], ln["instruct"], 4.0), 3: (tagged, ln["instruct"], 3.0)}
        for k in ln.get("variants") or range(1, jobs["variants"] + 1):
            def gen(path, k=k):
                text, instruction, scale = settings[k]
                req = {"id": "r", "text": text, "speaker": "S0", "ref_audio_path": ln["ref_wav"], "ref_text": ln["ref_text"]}
                if instruction:
                    req["instruction"] = instruction
                seed = 4000 + k
                set_all_seeds(seed)
                inputs = prepare_inputs(tokenizer, audio_tokenizer, model, [req], get_template(select_template_name(req)),
                                        guidance_scale=scale, guidance_scale_ref=None, guidance_scale_ins=None)
                n = 0
                with sf.SoundFile(str(path), mode="w", samplerate=runtime.sample_rate, channels=1, subtype="PCM_16") as f:
                    for chunk in runtime.iter_audio_chunks(inputs, request_id="r", seed=seed):
                        f.write(chunk.audio)
                        n += len(chunk.audio)
                return n / runtime.sample_rate
            rec.item(ln["id"], k, gen)
    rec.save()


if __name__ == "__main__":
    main()
