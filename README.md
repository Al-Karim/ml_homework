# Big Data & ML Pipeline — Oil Production Analytics

**Дисциплина:** Семинар наставника  
**Тема:** Big Data и ML  
**Преподаватель:** Владислав Шевченко

## Архитектура

```
PostgreSQL → ETL (Python) → MinIO (Parquet) → Jupyter → Superset
```

## Стек

| Сервис | Назначение | Порт |
|--------|-----------|------|
| PostgreSQL 15 | OLTP база данных | 5432 |
| MinIO | S3-совместимое хранилище | 9000 / 9001 (UI) |
| JupyterHub | Ноутбуки (pandas, sklearn) | 8888 |
| Apache Superset | BI-дашборды | 8088 |

## Структура проекта

```
project/
├── docker-compose.yml          # Инфраструктура
├── sql/
│   └── 01_init.sql             # Схема + данные (все таблицы)
├── etl/
│   └── extract_to_minio.py    # ETL скрипт (PostgreSQL → MinIO)
└── notebooks/
    ├── 01_etl_pipeline.ipynb           # ETL внутри Jupyter
    ├── 02_task1_production_analytics.ipynb  # Задание 1
    ├── 03_task2_ml_prediction.ipynb         # Задание 2 (ML)
    ├── 04_task3_anomaly_detection.ipynb     # Задание 3 (аномалии)
    └── 05_task4_logistics.ipynb             # Задание 4 (логистика)
```

## Быстрый старт

### 1. Запуск инфраструктуры

```bash
docker-compose up -d
```

Дождитесь запуска всех сервисов (~2-3 минуты).

### 2. Проверка сервисов

```bash
docker-compose ps
```

Все сервисы должны быть `healthy` или `running`.

### 3. Доступ к сервисам

| Сервис | URL | Логин | Пароль |
|--------|-----|-------|--------|
| Jupyter | http://localhost:8888 | — | — |
| MinIO Console | http://localhost:9001 | minioadmin | minioadmin123 |
| Superset | http://localhost:8088 | admin | admin |
| PostgreSQL | localhost:5432 | pipeline_user | pipeline_pass |

### 4. Выполнение ноутбуков

Откройте Jupyter по адресу http://localhost:8888, перейдите в папку `work/` и запускайте ноутбуки **по порядку**:

1. `01_etl_pipeline.ipynb` — ETL: PostgreSQL → MinIO
2. `02_task1_production_analytics.ipynb` — аналитика добычи
3. `03_task2_ml_prediction.ipynb` — прогноз дебита
4. `04_task3_anomaly_detection.ipynb` — детекция аномалий
5. `05_task4_logistics.ipynb` — анализ логистики

### 5. Настройка Superset

1. Войдите в Superset: http://localhost:8088 (admin/admin)
2. `Settings → Database Connections → + Database`
3. Выберите PostgreSQL, строка подключения:
   ```
   postgresql://pipeline_user:pipeline_pass@postgres:5432/oildb
   ```
4. Создайте датасеты из представлений:
   - `mart_production`
   - `mart_failures`  
   - `mart_logistics`
5. Создайте чарты (см. ниже)

#### Чарты для Задания 1 (mart_production)
- **Line chart**: X=date, Y=oil_ton, Color=well_name → «Добыча по времени»
- **Bar chart**: X=well_name, Y=SUM(oil_ton) → «Топ скважин»
- **Heatmap**: X=pressure, Y=oil_ton → «Давление vs Дебит»

#### Чарты для Задания 2 (mart_ml_predictions)
- **Line chart**: Actual vs Predicted → «Прогноз дебита»

#### Чарты для Задания 3 (mart_failures)
- **Table**: pump, failure_type, downtime_hours → «Отказы оборудования»

#### Чарты для Задания 4 (mart_logistics)
- **Bar chart**: weather → avg(delay_hours) → «Задержка vs Погода»
- **Scatter**: distance_km vs cost_usd → «Cost vs Distance»
- **Table**: driver KPI

## Данные

### Таблицы

| Таблица | Описание | Строк |
|---------|----------|-------|
| `wells` | Справочник скважин | 5 |
| `production` | Ежедневная добыча (окт 2025) | 150 |
| `well_telemetry` | Телеметрия по часам | 48 |
| `well_targets` | Целевой дебит для ML | 90 |
| `pumps` | Справочник насосов | 5 |
| `pump_sensors` | Данные датчиков | 72 |
| `pump_failures` | Факты отказов | 3 |
| `deliveries` | Поставки | 30 |
| `drivers` | Водители | 5 |
| `vehicles` | Транспорт | 5 |
| `oil_stations` | Нефтяные станции | 20 |

### Витрины (Views)

| View | Описание |
|------|----------|
| `mart_production` | Добыча + данные скважин |
| `mart_failures` | Отказы + данные насосов |
| `mart_logistics` | Поставки + водители + транспорт |

## ETL — запуск вне Jupyter

```bash
# Установить зависимости
pip install psycopg2-binary sqlalchemy boto3 pyarrow minio pandas

# Запустить
PG_HOST=localhost MINIO_ENDPOINT=localhost:9000 python etl/extract_to_minio.py
```

## Чек-лист

- [x] `docker-compose.yml` — инфраструктура (PostgreSQL, MinIO, Jupyter, Superset)
- [x] `sql/01_init.sql` — схема и данные всех таблиц
- [x] `etl/extract_to_minio.py` — ETL скрипт
- [x] `01_etl_pipeline.ipynb` — ETL с партиционированием Parquet
- [x] `02_task1_production_analytics.ipynb` — аналитика добычи + витрина
- [x] `03_task2_ml_prediction.ipynb` — Linear Regression + Random Forest (MAE/RMSE/R²)
- [x] `04_task3_anomaly_detection.ipynb` — Z-score + Isolation Forest + Risk Score
- [x] `05_task4_logistics.ipynb` — анализ задержек + KPI водителей
- [x] Superset дашборды — Delay vs Weather, Cost vs Distance, Driver KPI

## Скриншоты

Скриншоты находятся в папке `screenshots/` и подтверждают работу всех компонентов pipeline.

| Файл | Что показывает |
|------|----------------|
| `01_docker_containers.png` | Все 4 контейнера healthy |
| `02_jupyter_notebooks.png` | 5 запущенных ноутбуков |
| `03_minio_bucket.png` | Bucket oil-pipeline с parquet файлами |
| `04_superset_dashboard.png` | Дашборды с чартами |
| `05_notebook_etl.png` | Вывод ETL ноутбука |
| `06_notebook_ml.png` | Метрики ML модели (MAE/RMSE/R²) |
| `07_notebook_anomaly.png` | Аномалии и Risk Score |
