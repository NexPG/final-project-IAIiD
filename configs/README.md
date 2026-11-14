# Конфигурации

Здесь хранятся конфигурации обучения и сервиса в YAML/JSON.

Планируемые файлы:

```text
configs/
├── base.yaml                 # общие параметры
├── baseline.yaml             # TF-IDF + LogReg
├── linear_svc.yaml           # LinearSVC/ComplementNB
├── transformer.yaml          # optional DistilBERT/MiniLM experiment
└── service.yaml              # пороги, лимиты, routing
```

## Правила

1. Секреты и токены не хранятся в конфигурациях.
2. Конфиг эксперимента фиксируется в MLflow и в Git commit.
3. Пороговые значения confidence/margin выносятся в конфиг, а не в код.
4. Изменения конфигурации, влияющие на качество, отражаются в `docs/experiments.md`.
