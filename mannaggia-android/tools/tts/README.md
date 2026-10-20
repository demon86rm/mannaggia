# Audio dei santi con Chatterbox

Script per generare l'audio di "Mannaggia <santo>!" per tutti i santi di `app/src/main/assets/santi.txt`.

- **Modello:** [Chatterbox Multilingual](https://github.com/resemble-ai/chatterbox) (MIT).
- **Voce di riferimento:** `voce-riferimento.wav`, generata con Kokoro (Apache-2.0).

| File | Cosa fa |
|---|---|
| `genera_audio.py` | Generazione completa, riprendibile. Un WAV per santo, chiamato `sha1(santo)[:12].wav`, più `manifest.tsv`. |
| `prova_pronuncia.py` | Genera una frase con grafie diverse, per confrontarle a orecchio. |
| `pronuncia_auto.py` | Trova i nomi non italiani e propone una grafia "all'italiana" (Wikidata → lingua, espeak-ng → IPA, regole IPA → italiano). |
| `origine_santi.py` | Paese di nascita o cittadinanza da Wikidata. Il TSV prodotto serve a `pronuncia_auto.py --qid`. |
| `pronuncia.tsv` | Correzioni a mano (santo ⇥ testo da leggere). Hanno la precedenza su quelle automatiche. |

Parametri confermati a orecchio:
- exaggeration 0.6, cfg 0.5, temperature 0.5, top_p 0.9;
- 4 take, tenendo la più corta dopo il trim;
- trim a -25 dB all'inizio e -45 dB alla fine, con 150 ms di margine.

## Setup (Windows + WSL2 + Radeon, testato con RX 9070 XT)

1. **Windows:** driver AMD Adrenalin per WSL2 (26.2.2 o successivo). WSL con Ubuntu 22.04.
2. **ROCm, senza driver kernel** (in WSL il kernel è di Microsoft):
   ```sh
   wget https://repo.radeon.com/amdgpu-install/7.2.4/ubuntu/jammy/amdgpu-install_7.2.4.70204-1_all.deb
   sudo apt install ./amdgpu-install_7.2.4.70204-1_all.deb
   sudo amdgpu-install -y --usecase=rocm --no-dkms
   sudo usermod -a -G render,video $LOGNAME
   ```
3. **librocdxg 1.2.0**, la versione per ROCm 7.2.x:
   ```sh
   wget https://github.com/ROCm/librocdxg/releases/download/v1.2.0/rocdxg-roct_1.2.0_amd64.deb
   sudo dpkg -i rocdxg-roct_1.2.0_amd64.deb
   echo 'export HSA_ENABLE_DXG_DETECTION=1' >> ~/.bashrc
   ```
   Poi `wsl --shutdown` e riapri. `rocminfo | grep gfx` deve mostrare la GPU (gfx1201).
4. **venv con il PyTorch di AMD** (wheel cp310 da repo.radeon.com):
   ```sh
   sudo apt install -y python3-venv espeak-ng
   python3 -m venv ~/venv/tts && source ~/venv/tts/bin/activate
   B=https://repo.radeon.com/rocm/manylinux/rocm-rel-7.2.1
   pip install $B/torch-2.9.1%2Brocm7.2.1.lw.gitff65f5bc-cp310-cp310-linux_x86_64.whl \
               $B/torchaudio-2.9.0%2Brocm7.2.1.gite3c6ee2b-cp310-cp310-linux_x86_64.whl \
               $B/triton-3.5.1%2Brocm7.2.1.gita272dfa8-cp310-cp310-linux_x86_64.whl
   ```
5. **Chatterbox senza dipendenze**: chatterbox richiede torch 2.6.0, e un install normale sostituirebbe il PyTorch ROCm.
   ```sh
   pip install --no-deps chatterbox-tts==0.1.7
   pip install 'numpy>=1.24,<2' librosa==0.11.0 s3tokenizer transformers==5.2.0 diffusers==0.29.0 \
               resemble-perth conformer==0.3.2 safetensors==0.5.3 spacy-pkuseg pykakasi==2.3.0 \
               pyloudnorm omegaconf soundfile 'setuptools<81'
   python -c 'import torch; print(torch.__version__, torch.cuda.is_available())'   # +rocm7.2.1 True
   ```

## Uso

Dalla cartella `mannaggia-android`, con il venv attivo:
```sh
python tools/tts/genera_audio.py --limit 20     # prova: ~20 s a frase su RX 9070 XT
python tools/tts/genera_audio.py                # tutti (~30 h), riprende da dove si era fermato
```
L'output va in `~/mannaggia-audio`, fuori dal repo. Con il PC Windows in sospensione la generazione si ferma.
