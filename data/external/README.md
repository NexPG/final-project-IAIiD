# External datasets (local only)

This directory holds downloaded public corpora. Raw files are **not committed**
and must stay local because of size, licensing and PII.

**For running the API/demo the data is not included:** run the download and
training scripts described below; the model is generated locally as
`artifacts/model.joblib` and stays out of git.

Expected local files (not in git):

```text
data/external/
├── twcs/
│   ├── dev_cases.csv
│   └── dev_cases_pseudo_labeled.csv
├── bitext/
│   └── bitext.csv
└── audio_retailer/       # optional external generalisation check
```

## TWCS dev files

`dev_cases.csv` and `dev_cases_pseudo_labeled.csv` are generated from the public
Kaggle dataset
[Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter)
(SpotifyCares subset). They are not redistributed because of license/PII
constraints. The scripts download the official raw archive and rebuild both files:

```bash
python scripts/data/download_data.py --fetch-twcs
python scripts/data/prepare_twcs.py
```

Expected columns:

| `dev_cases.csv` | `dev_cases_pseudo_labeled.csv` |
|---|---|
| `case_id`, `customer_text`, `brand_response`, `conversation_id`, `created_at`, `brand` | same columns plus `intent`, `pseudo_label_method` |

Checksums and the exact source description are in
[`docs/01_task/data_card.md`](../../docs/01_task/data_card.md).

## Bitext

Download into `data/external/bitext/bitext.csv`:

```bash
python scripts/data/download_data.py --fetch-bitext
```

Expected columns: `instruction`, `category`, `intent`.

## Rules

- Do not commit raw tweets, customer texts or any PII.
- Mask handles, emails, phones and URLs before annotation.
- Record source URL, license and checksum in `data/manifest.json` and the data card.
- Delete local copies after the course defence if required.
