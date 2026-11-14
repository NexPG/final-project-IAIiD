# Данные и split

**Статус:** реализовано  
**Владелец:** Владимир Егоров  
**Связано:** [`TZ.md`](TZ.md), §6; [`data_card.md`](data_card.md)

## 1. Источники

| Источник | Строк | Язык | Роль |
|---|---|---|---|
| TWCS SpotifyCares | 5 732 | EN | реальный домен |
| Bitext Customer Support | 7 695 | EN | вспомогательный домен |
| Synthetic seed | 420 | RU | seed и редкие классы |
| **Всего** | **13 847** | mixed | один пул |

Сырые данные лежат в `data/external/` и не коммитятся.

## 2. 80/20 split

Все источники объединены, перемешаны и разделены **80/20**:

| Split | Строк | Доля |
|---|---|---|
| Train | 11 061 | 79.9% |
| Test | 2 786 | 20.1% |

Стратификация — одновременно по двум ключам:

```text
stratum = source + "||" + label
```

То есть сохраняются и классовые, и источниковые пропорции. Внутри каждого стратума split идёт по `conversation_id`, чтобы один диалог не попал в train и test.

| Источник | Train | Test |
|---|---|---|
| TWCS | 4 570 | 1 162 |
| Bitext | 6 155 | 1 540 |
| Synthetic | 336 | 84 |

`other` — 43.3% в train и 43.3% в test. Cap не применяется, чтобы не ломать стратификацию; дисбаланс компенсируется `class_weight=balanced`.

## 3. Почему нет validation

Отдельный validation не нужен:

- train — единственный источник для обучения, выбора модели и гиперпараметров;
- 5-fold `StratifiedGroupKFold` на train даёт OOF-оценку;
- `RandomizedSearchCV` подбирает гиперпараметры по CV;
- порог и margin выбираются по OOF;
- test открывается один раз после фиксации модели и порога.

Это сохраняет 20% данных для честной финальной проверки и не тратит ещё 10–15% на validation.

## 4. Маппинг в 7 классов

| Целевой класс | TWCS-интенты | Bitext-категории | Synthetic |
|---|---|---|---|
| `payment` | `billing_payment`; refund-часть `cancellation_refund` | PAYMENT, INVOICE, REFUND, CANCEL | Оплата |
| `subscription` | `subscription_plan`; cancellation-часть | SUBSCRIPTION, ORDER (cancel/change) | Подписка |
| `account` | `account_access`, `account_data_privacy` | ACCOUNT, CONTACT | Аккаунт |
| `app` | `playback_technical` | — | Приложение |
| `recommendations` | `feature_request_feedback` | FEEDBACK | Рекомендации |
| `content` | `content_availability` | — | Контент |
| `other` | `ads_free_tier_complaint`, `general_complaint_dissatisfaction`, `other` | ORDER (place/track), DELIVERY, SHIPPING | Другое |

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
| `label_quality` | enum | `weak`, `synthetic` |
| `source` | enum | `weak_twcs`, `bitext`, `synthetic` |
| `split` | enum | `train`, `test` |
| `conversation_id` | string | группа для split |
| `channel` | enum | twitter/app/email |
| `locale` | enum | en/ru/mixed |

## 6. Валидация

Pandas-проверки:

- обязательные поля и пропуски;
- допустимые классы/split/source;
- длина 10–5000;
- уникальность `id`;
- отсутствие cross-split дублей;
- отсутствие утечки `conversation_id`;
- PII-паттерны;
- достаточность классов в test.

Great Expectations: 8 expectations, отчёт `data/processed/ge_report.json`.

## 7. Приватность и версионирование

- Публичные твиты могут содержать PII; маскирование до обучения.
- Сырые данные не коммитятся.
- `data/manifest.json` хранит SHA-256 источников и версию датасета.
- `dataset_version` фиксируется в MLflow.

## 8. Ограничения

- Test-метки weak/synthetic, не human-verified.
- Overall test смешивает три источника; на TWCS macro-F1 ниже.
- Synthetic русскоязычный, TWCS/Bitext англоязычные.
- `content` и `app` редки.
- Лицензия TWCS требует уточнения.
