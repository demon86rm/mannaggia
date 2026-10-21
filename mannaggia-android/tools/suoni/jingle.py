#!/usr/bin/env python3
"""Jingle dei trofei: un arpeggio di campanelle (~1 s), sintetizzato da zero.

Quattro note ascendenti di Do maggiore (Do-Mi-Sol-Do) con il timbro di una
campanella: parziali non armoniche che decadono in fretta, piu' un filo di
riverbero. Seme fisso: il file si rigenera uguale.

Uso (venv con numpy, ffmpeg nel PATH; dalla cartella mannaggia-android):
    python tools/suoni/jingle.py --out app/src/main/res/raw/trofeo.ogg
"""

import argparse
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coro import SR, riverbero  # noqa: E402  (stesso riverbero del coro, piu' corto)

NOTE = [(1046.50, 0.00), (1318.51, 0.09), (1567.98, 0.18), (2093.00, 0.27)]  # C6 E6 G6 C7
# Campanella: (rapporto di frequenza, ampiezza, decadimento in s).
PARZIALI = [(1.0, 1.0, 0.45), (2.76, 0.45, 0.22), (5.40, 0.25, 0.12), (8.93, 0.12, 0.07)]
DURATA = 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=3)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    t = np.arange(int(SR * DURATA)) / SR
    mix = np.zeros_like(t)
    for i, (f, start) in enumerate(NOTE):
        tt = np.clip(t - start, 0, None)
        on = (t >= start).astype(float)
        gain = 1.0 if i < len(NOTE) - 1 else 1.3          # l'ultima nota un po' piu' forte
        for ratio, amp, decay in PARZIALI:
            mix += gain * amp * on * np.exp(-tt / decay) * np.sin(2 * np.pi * f * ratio * tt + rng.uniform(0, 6.28))
    mix = riverbero(mix, rng, rt=0.8, mix=0.25)
    mix[-int(0.15 * SR):] *= np.linspace(1, 0, int(0.15 * SR))
    mix *= 10 ** (-3 / 20) / np.max(np.abs(mix))          # -3 dBFS: piu' discreto del coro
    pcm = (mix * 32767).astype("<i2")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "jingle.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                        "-c:a", "libvorbis", "-q:a", "4", str(out)], check=True)
    print(f"{out}: {len(pcm) / SR:.1f} s, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
