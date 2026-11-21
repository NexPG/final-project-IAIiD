# Docker

## One-command startup

Docker Compose поднимает `api`, Prometheus и Grafana, а также одноразовый
`trainer`, который сам скачивает данные и обучает модель.

Сначала задайте Kaggle API token (нужен для TWCS):

```powershell
# Windows PowerShell
$env:KAGGLE_USERNAME="your_username"
$env:KAGGLE_KEY="your_api_key"
```

```bash
# Linux/macOS
export KAGGLE_USERNAME=your_username
export KAGGLE_KEY=your_api_key
```

Затем из корня репозитория:

```bash
docker compose -f docker/docker-compose.yml up --build
```

Что произойдёт:

1. `trainer` скачает Bitext с Hugging Face и TWCS с Kaggle.
2. `prepare_twcs.py` соберёт `dev_cases.csv` и pseudo-label файл.
3. `build_dataset.py` соберёт датасет.
4. `train_final.py` обучит финальную модель в `artifacts/model.joblib`.
5. `api` дождётся успешного завершения trainer и запустится.

Первый запуск долгий: TWCS — около 500 МБ, плюс обучение на CPU. Повторный
`up` использует уже скачанные данные и готовую модель.

Если данные и модель уже есть на хосте, trainer завершится быстро.

## Проверка

```bash
python scripts/service/smoke.py --base-url http://127.0.0.1:8000
```

Grafana: `http://localhost:3000` (`admin` / `admin`).

Остановка:

```bash
docker compose -f docker/docker-compose.yml down
```

Если trainer упал, смотрите:

```bash
docker compose -f docker/docker-compose.yml logs trainer
```

Частая причина — не заданы `KAGGLE_USERNAME`/`KAGGLE_KEY`.

## Файлы

```text
docker/
├── Dockerfile
└── docker-compose.yml
```

- Multi-stage сборка, `python:3.12-slim`, non-root, healthcheck.
- Модель и конфиги монтируются read-only.
- `data/` и `artifacts/` — bind-mount, чтобы данные и модель оставались на хосте.
- Секреты не попадают в образ.
- CI на GitHub Actions проверяет `ruff`, `mypy`, `pytest`; Docker build и smoke — локально.
