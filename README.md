# MarathiTTSv1 — Marathi Text-to-Speech

A Marathi TTS training pipeline using [Piper](https://github.com/rhasspy/piper) and the VITS architecture.
Trained on [OpenSLR-64](https://openslr.org/64/), designed for offline Raspberry Pi deployment.

> **New here?** See [STEP_BY_STEP_GUIDE.md](STEP_BY_STEP_GUIDE.md) for a complete walkthrough.

## What Was Fixed in This Release

| Issue | Fix Applied |
|---|---|
| `ModuleNotFoundError: No module named 'pkg_resources'` | `setuptools` added to `requirements.txt`; `fix_environment.bat` script provided; `pytorch-lightning` upgraded to 2.4+ (lightning_fabric 2.3+ no longer imports pkg_resources) |
| `pytorch-lightning` version conflict (`<2.0.0` vs `>=2.4.0`) | Both `requirements.txt` files now consistently specify `>=2.4.0,<3.0.0` |
| No Windows setup script | `scripts/setup_piper.bat` added — full one-click Windows setup |
| `train.bat` crashes silently on environment errors | Pre-flight checks added with clear error messages and exact fix commands |
| Text normalizer missing decimal/date/ordinal/currency support | `normalize_marathi.py` v2: decimals, DD/MM/YYYY dates, ordinals (1ला→पहिला), currency (₹,Rs.), negatives, number ranges, year ranges |
| Abbreviation dictionary limited to 10 entries | Expanded to 30 entries: units, legal titles, organisations |

## Quick Start — Windows

```powershell
python -m venv venv && venv\Scripts\activate
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
scripts\setup_piper.bat
python scripts\download_dataset.py
python scripts\format_data.py
scripts\train.bat
```

If you see `ModuleNotFoundError: No module named 'pkg_resources'` run `scripts\fix_environment.bat`.

## Quick Start — Linux / Colab

```bash
chmod +x scripts/setup_piper.sh && ./scripts/setup_piper.sh
python scripts/download_dataset.py && python scripts/format_data.py
python scripts/download_checkpoint.py   # for fine-tuning
./scripts/train.sh
```

## Deploy on Raspberry Pi

```bash
pip install piper-tts
echo "नमस्कार, कसे आहात?" | piper --model marathi-medium.onnx --length_scale 1.2 --output_file out.wav
aplay out.wav
```

## License

Dataset: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (OpenSLR-64) | Piper: [MIT](https://github.com/rhasspy/piper/blob/master/LICENSE)
