# External datasets (local only)

This directory holds downloaded public corpora. Raw files are **not committed**
and must stay local because of size, licensing and PII.

**For running the API/demo these files are not needed:** the trained model is
committed as [`artifacts/model.joblib`](../../artifacts/model.joblib). The files
below are only required to rebuild the dataset or retrain the model.

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

`dev_cases.csv` and `dev_cases_pseudo_labeled.csv` are team-derived artifacts from
the public Kaggle dataset
[Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter)
(SpotifyCares subset). They are not a single downloadable Kaggle file and are not
redistributed because of license/PII constraints.

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
