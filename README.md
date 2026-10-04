# Kvitto Payments API

[![CI](https://github.com/Icestorm203/kvitto-payments-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Icestorm203/kvitto-payi/actions/workflows/ci.yml)

FastAPI-сервис для создания платежей, управления тарифами и обработки банковских вебхуков. Проект хранит данные в PostgreSQL и поддерживает промокоды, рассрочку и идемпотентность запросов.

## Основные возможности

- Получение списка тарифов
- Создание и получение платежей
- Поддержка промокодов
- Поддержка рассрочки на 3, 6 и 12 месяцев
- Идемпотентное создание платежей
- Обработка банковских вебхуков
- PostgreSQL + SQLAlchemy ORM
- Docker Compose
- 30 интеграционных тестов
- Ruff и GitHub Actions CI

## Endpoints

| Метод | Endpoint | Описание |
|---------|---------|---------|
| GET | /tariffs | Получить список тарифов |
| POST | /payments | Создать платеж |
| GET | /payments/{payment_id} | Получить платеж по ID |
| POST | /webhooks/bank | Изменить статус платежа через вебхук |

## Технологии

- Python 3.12
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- Docker / Docker Compose
- Pytest

## Структура проекта

```text
.
├── app/
│   ├── constants.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── services.py
│   └── routers/
│       ├── payments.py
│       ├── tariffs.py
│       └── webhooks.py
├── docker/
│   └── init.sql
├── tests/
│   ├── conftest.py
│   ├── test_payments.py
│   ├── test_tariffs.py
│   └── test_webhooks.py
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── requirements.txt
├── .env.example
├── ruff.toml
└── README.md
```

> В проекте используется PostgreSQL. При старте приложения автоматически создаются таблицы и наполняются тарифы.

## Требования

- Python 3.12+
- PostgreSQL 17+
- Docker и Docker Compose (опционально)

## Настройка окружения

Создайте `.env` в корне проекта (можно использовать `.env.example` как шаблон):

```env
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=kvitto
DB_USER=postgres
DB_PASSWORD=postgres

TEST_DB_HOST=127.0.0.1
TEST_DB_PORT=5432
TEST_DB_NAME=kvitto_test
TEST_DB_USER=postgres
TEST_DB_PASSWORD=postgres
```

Если вы планируете использовать Docker Compose, значения уже настроены в `docker-compose.yml`.

## Запуск локально

1. Создайте и активируйте виртуальное окружение:

```bash
python -m venv .venv
source .venv/bin/activate
```

Для Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Запустите PostgreSQL и создайте базы `kvitto` и `kvitto_test`.

4. Запустите сервер:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

После запуска API будет доступен по адресу:

- http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Запуск через Docker Compose

```bash
docker compose up --build
```

Это поднимет:

- PostgreSQL на порту `5433`
- API на порту `8000`

Swagger UI будет доступен по адресу:

http://localhost:8000/docs

## Тарифы

При инициализации приложения автоматически добавляются 3 тарифа:

```json
[
  {"id": 1, "title": "basic", "price": 990000},
  {"id": 2, "title": "standard", "price": 1990000},
  {"id": 3, "title": "premium", "price": 2990000}
]
```

### Получить список тарифов

```http
GET /tariffs
```

Пример ответа:

```json
[
  {
    "id": 1,
    "title": "basic",
    "price": 990000
  },
  {
    "id": 2,
    "title": "standard",
    "price": 1990000
  }
]
```

## Платежи

### Создать платеж

```http
POST /payments
Content-Type: application/json
```

Тело запроса:

```json
{
  "tariff_id": 2,
  "email": "user@example.com",
  "method": "card",
  "promo_code": "KVITTO10"
}
```

Поддерживаемые методы оплаты:

- `card`
- `sbp`
- `installment`

Если метод `installment`, поле `installment_months` обязательно:

```json
{
  "tariff_id": 2,
  "email": "user@example.com",
  "method": "installment",
  "installment_months": 3
}
```

Допустимые значения `installment_months`: `3`, `6`, `12`.

### Промокод

Промокод включен в проекте и проверяется без учета регистра:

- `KVITTO10`
- `kvitto10`
- `KvItTo10`

Скидка: `10%` от стоимости тарифа.

### Идемпотентность

Для защиты от повторного создания платежа используется заголовок:

```http
Idempotency-Key: some-unique-key
```

Если тот же ключ отправлен повторно, API вернет уже созданный платеж с кодом `200 OK` вместо создания новой записи.

### Получить платеж по ID

```http
GET /payments/{payment_id}
```

Пример ответа:

```json
{
  "id": 1,
  "status": "pending",
  "tariff_id": 2,
  "amount": 1990000,
  "discount": 0,
  "method": "card",
  "installment_months": null,
  "schedule": null,
  "email": "user@example.com",
  "created_at": "2026-10-04T12:00:00+00:00"
}
```

## Распределение платежей по графику рассрочки

Для метода `installment` сервис вычисляет равномерный график платежей на указанное количество месяцев. Сумма всех выплат равна итоговой стоимости товара, а разница между соседними платежами не превышает 1 копейку.

Пример:

```json
{
  "amount": 1990000,
  "installment_months": 3,
  "schedule": [663334, 663333, 663333]
}
```

## Вебхуки банка

### Обновить статус платежа

```http
POST /webhooks/bank
Content-Type: application/json
```

Тело запроса:

```json
{
  "payment_id": 1,
  "status": "succeeded"
}
```

Допустимые статусы:

- `pending`
- `succeeded`
- `failed`
- `refunded`

Правила переходов:

- `pending -> succeeded`
- `pending -> failed`
- `succeeded -> refunded`

Некорректные переходы возвращают `409 Conflict`.

Пример ответа:

```json
{
  "result": "ok"
}
```

## Тестирование

Локальный запуск:
```bash
pytest
```

Запуск внутри Docker:
```bash
docker compose exec api pytest
```

Проект содержит 30 интеграционных тестов (Pytest).

Покрытые сценарии:

- тарифы
- создание платежей
- промокоды
- рассрочка
- идемпотентность
- вебхуки
- переходы статусов
- ошибки 404/409/422

## CI/CD

На каждый push и pull request автоматически запускаются:

- Ruff (lint)
- Pytest (integration tests)

GitHub Actions поднимает PostgreSQL и выполняет полный прогон тестов.

## Полезные ссылки

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

