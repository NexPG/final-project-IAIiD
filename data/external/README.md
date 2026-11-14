# External datasets (local only)

This directory holds downloaded public corpora. Raw files are **not committed**
and must stay local because of size, licensing and PII.

Expected local files (not in git):

```text
data/external/
├── twcs/                 # Customer Support on Twitter (SpotifyCares subset)
├── bitext/               # Bitext customer-support dataset
└── audio_retailer/       # optional external generalisation check
```

Rules:

- Download with `scripts/download_data.py` and verify SHA-256.
- Do not commit raw tweets or any PII.
- Mask handles, emails, phones and URLs before annotation.
- Record source URL, license and checksum in `data/manifest.json` and the data card.
- Delete local copies after the course defence if required.
