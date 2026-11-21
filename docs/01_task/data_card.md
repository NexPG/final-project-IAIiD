# Data card

**Версия:** 2026-11-14  
**Dataset version:** `sha256:d997f61924c8ea486dba05eb5ae017252d5ad896c2872c87c44abff34ca601db`  
**Владелец:** Владимир Егоров

## 1. Происхождение

| Источник | Лицензия | Роль | Локальный путь |
|---|---|---|---|
| TWCS SpotifyCares | CC BY-NC-SA 4.0 (Kaggle; commercial use — contact author) | реальный домен | `data/external/twcs/` |
| Bitext Customer Support | CDLA-Sharing-1.0 | вспомогательный домен | `data/external/bitext/` |

Сырые данные не коммитятся. Checksums фиксируются в `data/manifest.json`.

Как получить данные:

```bash
python scripts/data/download_data.py --fetch-bitext
python scripts/data/download_data.py --fetch-twcs   # нужен Kaggle API token
python scripts/data/prepare_twcs.py
```

`prepare_twcs.py` собирает `dev_cases.csv` и `dev_cases_pseudo_labeled.csv` из raw
Kaggle-архива. Модель обучается локально через `scripts/train/train_final.py` и
также не коммитится.

## 2. Объём и split

TWCS и Bitext объединены в один пул, перемешаны и разделены **80/20** со стратификацией одновременно по `(source, label)`.

| Split | Строк | Доля |
|---|---|---|
| Train | 10 713 | 79.8% |
| Test | 2 714 | 20.2% |
| **Всего** | **13 427** | 100% |

| Источник | Train | Test | Доля test |
|---|---|---|---|
| TWCS weak | 4 558 | 1 174 | 20.5% |
| Bitext mapped | 6 155 | 1 540 | 20.0% |

Пропорции источников и классов сохранены. Validation не выделяется: его роль выполняет 5-fold CV на train.

## 3. Распределение классов

| Класс | Train | Test |
|---|---|---|
| `payment` | 1 748 | 441 |
| `subscription` | 1 322 | 330 |
| `account` | 1 671 | 418 |
| `app` | 197 | 54 |
| `recommendations` | 1 034 | 259 |
| `content` | 17 | 5 |
| `other` | 4 724 | 1 207 |

`other` — 44.1% в train и 44.5% в test. Cap не применяется, чтобы сохранить стратификацию; дисбаланс компенсируется `class_weight=balanced`.

## 4. Качество меток

| Тип | Доля |
|---|---|
| `weak` | 100% |

- TWCS: keyword/pseudo-label → 11 weak-интентов → 7 классов.
- Bitext: маппинг категорий/интентов.

**Ограничение:** test-метрики измеряют согласие с weak-метками, а не с независимой человеческой разметкой. Это явно указано в отчёте.

## 5. Очистка и PII

- HTML unescape, NFKC, нормализация кавычек/пробелов.
- Удаление URL и @mentions.
- Маскирование email, телефона, card-like последовательностей.
- Дедупликация по нормализованному Unicode-тексту до split.
- Split по `conversation_id`, чтобы один диалог не попал в train и test.

## 6. Известные смещения

- TWCS — публичные сообщения 2017 года.
- Bitext — retail/support, не музыкальный стриминг.
- `content` и `app` редки.
- Test смешивает два источника, поэтому overall-метрика выше, чем только на TWCS.

## 7. Checksums

| Файл | SHA-256 |
|---|---|
| `twcs/dev_cases.csv` | `b6207f4159695823d27bb45c412cf2d9a2bb166302074ebbdaccdb876981d02b` |
| `twcs/dev_cases_pseudo_labeled.csv` | `f803059b4ea3c4a54c37334c4ed6885633812e2c713095776c62d56a57ab6ea5` |
| `bitext/bitext.csv` | `6f81102b0100b97b8468eb04368033a23206bf1fde9d53500d5806ec1001a434` |
