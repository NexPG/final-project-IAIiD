# Данные

Содержимое `external/`, `raw/`, `interim/`, `processed/` и `feedback/` не коммитится,
кроме `.gitkeep` и README.

```text
data/
├── external/     # TWCS, Bitext и другие локальные источники
├── raw/          # исходные данные
├── interim/      # промежуточные результаты
├── processed/    # train/test после 80/20 split
├── feedback/     # подтверждения и исправления операторов
└── manifest.json # checksum и версия датасета
```

## Текущий набор

- TWCS SpotifyCares + Bitext.
- 13 427 строк; 10 713 train / 2 714 test.
- 80/20, стратификация по `(source, label)`.
- Synthetic исключён.
- Test frozen, открывается один раз.

## Правила

1. Реальные PII маскируются; сырые данные не коммитятся.
2. Test замораживается и не используется для подбора.
3. Synthetic/weak-метки не выдаются за human ground truth.
4. Перед обучением запускается `validate_data.py` и `validate_data_ge.py`.
5. Каждый эксперимент фиксирует версию датасета и checksum манифеста.
6. Большие файлы не коммитятся.

## Схема

| Поле | Тип | Обязательно |
|---|---|---|
| `id` | string | да |
| `text` | string | да |
| `label` | enum | да |
| `label_quality` | enum | да |
| `source` | enum | да |
| `split` | enum | да |
| `conversation_id` | string | да |
| `channel` | enum | да |
| `locale` | enum | да |

Подробности — в [`docs/01_task/data.md`](../docs/01_task/data.md).
