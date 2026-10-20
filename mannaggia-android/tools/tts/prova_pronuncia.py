#!/usr/bin/env python3
"""Confronta grafie alternative di un santo dal nome difficile, con l'assetto di genera_audio.py.

Uso:
    python prova_pronuncia.py                                   # varianti di "Alruna"
    python prova_pronuncia.py --varianti 'Alruna,Al-runa'       # grafie a scelta

Crea ~/mannaggia-audio-prove/NN-<grafia>.wav per ogni variante.
"""

import argparse
from pathlib import Path

import soundfile as sf
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

from genera_audio import HERE, trim

VARIANTI = ["Alruna", "Al-runa", "Al runa", "Àlruna", "Allruna", "Alerruna"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frase", default="Mannaggia Beata {} di Cham!", help="{} = variante")
    ap.add_argument("--varianti", help="grafie separate da virgola")
    ap.add_argument("--ref", default=str(HERE / "voce-riferimento.wav"))
    ap.add_argument("--out", default=str(Path.home() / "mannaggia-audio-prove"))
    ap.add_argument("--takes", type=int, default=4)
    args = ap.parse_args()

    varianti = [v.strip() for v in args.varianti.split(",")] if args.varianti else VARIANTI
    out = Path(args.out)
    out.mkdir(exist_ok=True)

    model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
    model.prepare_conditionals(args.ref, exaggeration=0.6)

    for n, v in enumerate(varianti, 1):
        text = args.frase.format(v)
        takes = []
        for _ in range(args.takes):
            wav = model.generate(text, language_id="it", exaggeration=0.6,
                                 cfg_weight=0.5, temperature=0.5, top_p=0.9)
            takes.append(trim(wav, model.sr, -25.0, -45.0))
        best = min(takes, key=lambda w: w.shape[-1])
        name = out / f"{n:02d}-{v.replace(' ', '_')}.wav"
        sf.write(str(name), best[0].cpu().numpy(), model.sr)
        print(f"{name}  <-  {text}", flush=True)


if __name__ == "__main__":
    main()
