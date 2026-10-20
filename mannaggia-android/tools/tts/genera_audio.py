#!/usr/bin/env python3
"""Genera l'audio di "Mannaggia <santo>!" per tutti i santi dell'app, con Chatterbox.

Uso (dal venv con chatterbox-tts e PyTorch ROCm/CUDA):
    python tools/tts/genera_audio.py --out ~/mannaggia-audio
    python tools/tts/genera_audio.py --out ~/mannaggia-audio --limit 20   # prova su poche frasi

Riprende da dove si era fermato: le frasi gia' presenti in --out vengono saltate.
Il file di ogni santo si chiama <sha1(nome)[:12]>.wav, cosi' l'app puo' ricavarlo
dal nome. manifest.tsv elenca file e testo.

Parametri di default: quelli confermati nei test (2026-10-20).
"""

import argparse
import hashlib
import time
from pathlib import Path

import soundfile as sf
import torch
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

HERE = Path(__file__).resolve().parent


def file_id(saint: str) -> str:
    return hashlib.sha1(saint.encode("utf-8")).hexdigest()[:12]


def trim(wav, sr, start_db, end_db, start_pad_ms=60, end_pad_ms=150, fade_ms=30):
    """Remove breaths/silence around the speech (energy-based).

    The start uses a high threshold to drop breaths before the phrase; the end uses
    a much lower one so the decaying final vowel is kept, then fades out.
    """
    frame = int(sr * 0.02)
    x = wav[0]
    energy = x[: len(x) // frame * frame].reshape(-1, frame).pow(2).mean(dim=1).sqrt()
    db = 20 * torch.log10(energy + 1e-9)
    loud_start = (db > start_db).nonzero()
    loud_end = (db > end_db).nonzero()
    if len(loud_start) == 0:
        return wav
    start = max(0, loud_start[0].item() * frame - int(sr * start_pad_ms / 1000))
    end = min(len(x), (loud_end[-1].item() + 1) * frame + int(sr * end_pad_ms / 1000))
    out = wav[:, start:end].clone()
    fade = min(int(sr * fade_ms / 1000), out.shape[-1])
    out[:, -fade:] *= torch.linspace(1.0, 0.0, fade)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--santi", default=str(HERE.parent.parent / "app/src/main/assets/santi.txt"),
                    help="santi.txt dell'app (un santo per riga, # = commento)")
    ap.add_argument("--ref", default=str(HERE / "voce-riferimento.wav"), help="WAV della voce di riferimento")
    ap.add_argument("--out", default=str(Path.home() / "mannaggia-audio"), help="fuori dal repo: sono ~5400 WAV")
    ap.add_argument("--exaggeration", type=float, default=0.6)
    ap.add_argument("--cfg", type=float, default=0.5)
    ap.add_argument("--temperature", type=float, default=0.5)
    ap.add_argument("--top_p", type=float, default=0.9)
    ap.add_argument("--trim_db", type=float, default=-25.0, help="soglia di taglio all'inizio (respiri)")
    ap.add_argument("--trim_end_db", type=float, default=-45.0, help="soglia di taglio alla fine (bassa: tiene la coda della vocale)")
    ap.add_argument("--end_pad_ms", type=int, default=150)
    ap.add_argument("--takes", type=int, default=4)
    ap.add_argument("--limit", type=int, help="genera solo le prime N frasi mancanti")
    args = ap.parse_args()

    saints = [s.strip() for s in Path(args.santi).read_text(encoding="utf-8").splitlines()
              if s.strip() and not s.startswith("#")]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    with open(out / "manifest.tsv", "w", encoding="utf-8") as manifest:
        for s in saints:
            manifest.write(f"{file_id(s)}.wav\tMannaggia {s}!\n")

    todo = [s for s in saints if not (out / f"{file_id(s)}.wav").exists()]
    print(f"{len(saints)} santi, {len(saints) - len(todo)} gia' fatti, {len(todo)} da generare")
    if args.limit:
        todo = todo[: args.limit]
    if not todo:
        return

    # ROCm (AMD) and CUDA (NVIDIA) both show up as "cuda" in PyTorch.
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"dispositivo: {device}")
    model = ChatterboxMultilingualTTS.from_pretrained(device=device)
    model.prepare_conditionals(args.ref, exaggeration=args.exaggeration)

    started = time.time()
    for n, saint in enumerate(todo, 1):
        text = f"Mannaggia {saint}!"
        takes = []
        for _ in range(args.takes):
            wav = model.generate(text, language_id="it", exaggeration=args.exaggeration,
                                 cfg_weight=args.cfg, temperature=args.temperature, top_p=args.top_p)
            takes.append(trim(wav, model.sr, args.trim_db, args.trim_end_db, end_pad_ms=args.end_pad_ms))
        # Breaths and sighs make a take longer: keep the shortest one.
        best = min(takes, key=lambda w: w.shape[-1])
        # Write to a temp name first so an interrupted run never leaves a half file.
        final = out / f"{file_id(saint)}.wav"
        tmp = final.with_suffix(".tmp.wav")
        # soundfile instead of torchaudio.save: torchaudio >= 2.9 needs torchcodec for it.
        sf.write(str(tmp), best[0].cpu().numpy(), model.sr)
        tmp.rename(final)

        elapsed = time.time() - started
        eta = elapsed / n * (len(todo) - n)
        print(f"[{n}/{len(todo)}] {text}  (fine stimata tra {eta / 3600:.1f} h)", flush=True)


if __name__ == "__main__":
    main()
