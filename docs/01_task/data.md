# Данные и split

**Статус:** реализовано  
**Владелец:** Владимир Егоров  
**Связано:** [`TZ.md`](TZ.md), §6; [`data_card.md`](data_card.md)

## 1. Источники

| Источник | Строк | Язык | Роль |
|---|---|---|---|
| TWCS SpotifyCares | 5 732 | EN | реальный домен |
| Bitext Customer Support | 7 695 | EN | вспомогательный домен |
| **Всего** | **13 427** | EN | один пул |

Сырые данные лежат в `data/external/` и не коммитятся. Synthetic исключён: реальных данных достаточно, а synthetic добавлял русский шаблонный шум.

## 2. 80/20 split

Источники объединены, перемешаны и разделены **80/20**:

| Split | Строк | Доля |
|---|---|---|
| Train | 10 713 | 79.8% |
| Test | 2 714 | 20.2% |

Стратификация — одновременно по двум ключам:

```text
stratum = source + "||" + label
```

Сохраняются и классовые, и источниковые пропорции. Внутри стратума split идёт по `conversation_id`, чтобы один диалог не попал в train и test.

| Источник | Train | Test |
|---|---|---|
| TWCS | 4 558 | 1 174 |
| Bitext | 6 155 | 1 540 |

`other` — 44.1% в train и 44.5% в test. Cap не применяется; дисбаланс компенсируется `class_weight=balanced`.

## 3. Почему нет validation

- train — источник для обучения, выбора модели и гиперпараметров;
- 5-fold `StratifiedGroupKFold` на train даёт OOF-оценку;
- `HalvingRandomSearchCV` подбирает гиперпараметры по CV;
- порог и margin выбираются по OOF;
- test открывается один раз после фиксации модели и порога.

## 4. Маппинг в 7 классов

| Целевой класс | TWCS-интенты | Bitext-категории |
|---|---|---|
| `payment` | `billing_payment`; refund-часть `cancellation_refund` | PAYMENT, INVOICE, REFUND, CANCEL |
| `subscription` | `subscription_plan`; cancellation-часть | SUBSCRIPTION, ORDER (cancel/change) |
| `account` | `account_access`, `account_data_privacy` | ACCOUNT, CONTACT |
| `app` | `playback_technical` | — |
| `recommendations` | `feature_request_feedback` | FEEDBACK |
| `content` | `content_availability` | — |
| `other` | `ads_free_tier_complaint`, `general_complaint_dissatisfaction`, `other` | ORDER (place/track), DELIVERY, SHIPPING |

Спорные правила:

- `cancellation_refund` с refund/chargeback → `payment`, иначе `subscription`;
- Bitext ORDER про доставку → `other`;
- «не могу войти, чтобы отменить» → `account`, если главная проблема вход;
- «пропал трек» → `content`, если исчез из каталога; `app`, если не играет.

## 5. Схема записи

| Поле | Тип | Комментарий |
|---|---|---|
| `id` | string | стабильный ID |
| `text` | string | очищенный текст |
| `label` | enum | 7 классов |
| `label_quality` | enum | `weak` |
| `source` | enum | `weak_twcs`, `bitext` |
| `split` | enum | `train`, `test` |
| `conversation_id` | string | группа для split |
| `channel` | enum | web/email/social/app |
| `locale` | enum | en |

## 6. Валидация

- обязательные поля и пропуски;
- допустимые классы/split/source;
- длина 10–5000;
- уникальность `id`;
- отсутствие cross-split дублей;
- отсутствие утечки `conversation_id`;
- PII-паттерны;
- достаточность классов в test.

Great Expectations: 8 expectations, отчёт `data/processed/ge_report.json`; `--dirty` копия должна быть отклонена (поймано 4 нарушения).

## 7. Приватность и версионирование

- Публичные сообщения могут содержать PII; маскирование до обучения.
- Сырые данные не коммитятся.
- `data/manifest.json` хранит SHA-256 источников и версию датасета.
- `dataset_version` фиксируется в MLflow.

## 8. Ограничения

- Test-метки weak, не human-verified.
- Overall test смешивает два источника; на TWCS macro-F1 ниже.
- `content` и `app` редки.
- Лицензия TWCS: CC BY-NC-SA 4.0; commercial use требует контакта с автором.
