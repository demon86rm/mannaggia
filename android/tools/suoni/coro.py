#!/usr/bin/env python3
"""Coro angelico per i santi leggendari, sintetizzato da zero (nessun campione registrato).

Un accordo di Re maggiore cantato su "aah": per ogni nota qualche voce leggermente
stonata, con armoniche pesate sulle formanti della vocale "a" e vibrato; un
luccichio acuto a meta'; riverbero da chiesa. Seme fisso: il file si rigenera uguale.

Uso (venv con numpy, ffmpeg nel PATH; dalla cartella android):
    python tools/suoni/coro.py --out app/src/main/res/raw/coro.ogg
"""

import argparse
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

SR = 44100
# Breve: un "Aaah!" di un istante, non un brano. Durata prima della coda del riverbero.
DURATA = 1.5
ATTACCO, RILASCIO = 0.18, 0.7
RT = 1.4              # coda del riverbero, secondi
# Re maggiore aperto, dal basso all'alto: D3 A3 D4 F#4 A4 D5 (le acute entrano appena dopo).
NOTE = [(146.83, 0.0), (220.00, 0.0), (293.66, 0.03), (369.99, 0.06), (440.00, 0.09), (587.33, 0.12)]
VOCI_PER_NOTA = 4
FORMANTI = [(750, 180, 1.0), (1200, 260, 0.55), (2600, 400, 0.18)]  # vocale "a": (Hz, larghezza, peso)


def inviluppo(t, inizio, durata):
    """Slow attack from [inizio], sustain, slow release at the end (raised cosine)."""
    e = np.zeros_like(t)
    a = np.clip((t - inizio) / ATTACCO, 0, 1)
    e = 0.5 - 0.5 * np.cos(np.pi * a)
    fine = durata - RILASCIO
    r = np.clip((t - fine) / RILASCIO, 0, 1)
    return e * (0.5 + 0.5 * np.cos(np.pi * r))


def voce(t, f0, rng, inizio):
    """One "aah" voice: harmonics shaped by the vowel formants, with delayed vibrato."""
    detune = 2 ** (rng.uniform(-9, 9) / 1200)
    f = f0 * detune
    vib_freq = rng.uniform(4.6, 5.6)
    vib_depth = rng.uniform(0.002, 0.004)
    vib_on = np.clip((t - inizio - 0.2) / 0.5, 0, 1)   # il vibrato arriva dopo l'attacco
    inst = f * (1 + vib_depth * vib_on * np.sin(2 * np.pi * vib_freq * t + rng.uniform(0, 6.28)))
    phase = 2 * np.pi * np.cumsum(inst) / SR
    out = np.zeros_like(t)
    k = 1
    while k * f < 7000:
        hz = k * f
        peso = 0.08 + sum(w * np.exp(-((hz - c) / bw) ** 2) for c, bw, w in FORMANTI)
        out += (peso / k ** 0.7) * np.sin(k * phase + rng.uniform(0, 6.28))
        k += 1
    return out * inviluppo(t, inizio, DURATA)


def luccichio(t, rng):
    """A soft high shimmer (like little bells) fading in halfway."""
    out = np.zeros_like(t)
    for hz in (1174.66, 1479.98, 1760.0, 2349.32):
        trem = 0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(5, 8) * t + rng.uniform(0, 6.28))
        out += np.sin(2 * np.pi * hz * t) * trem
    env = np.clip((t - 0.25) / 0.4, 0, 1) * inviluppo(t, 0, DURATA)
    return 0.04 * out * env


def riverbero(x, rng, rt=RT, mix=0.35):
    """Church-like reverb: convolution with exponentially decaying noise."""
    n = int(SR * rt)
    tt = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-6.9 * tt / rt)   # -60 dB at rt
    ir[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))  # pre-delay morbido
    ir /= np.sqrt(np.sum(ir ** 2))
    size = len(x) + n
    wet = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)
    dry = np.concatenate([x, np.zeros(n)])
    return (1 - mix) * dry + mix * wet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="file .ogg (Vorbis) o .wav")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    t = np.arange(int(SR * DURATA)) / SR
    mix = np.zeros_like(t)
    for f0, inizio in NOTE:
        for _ in range(VOCI_PER_NOTA):
            mix += voce(t, f0, rng, inizio)
    mix += luccichio(t, rng) * VOCI_PER_NOTA * len(NOTE) / 6
    mix = riverbero(mix, rng)
    # Fade the reverb tail to silence and normalise to -1 dBFS.
    mix[-int(0.2 * SR):] *= np.linspace(1, 0, int(0.2 * SR))
    mix *= 10 ** (-1 / 20) / np.max(np.abs(mix))
    pcm = (mix * 32767).astype("<i2")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "coro.wav" if out.suffix != ".wav" else out
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        if out.suffix != ".wav":
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                            "-c:a", "libvorbis", "-q:a", "4", str(out)], check=True)
    print(f"{out}: {len(pcm) / SR:.1f} s, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
