# GBank

Учебное веб-приложение «банка» на Flask: регистрация и вход, профиль с балансом, переводы между пользователями, история транзакций и рейтинг «Топ-10 богачей».

> ⚠️ Приложение содержит намеренные уязвимости (SQL-инъекция в переводах, SSTI в `/add_money`) и предназначено только для обучения и CTF. Не разворачивайте его в открытом доступе.

## Стек

- Python 3.12, Flask 3
- Flask-Login, Flask-WTF, Flask-SQLAlchemy
- SQLite (`instance/bank.db`, поставляется с демо-данными)
- Gunicorn (в Docker)

## Демо-данные

В комплекте база с тестовой учётной записью для входа:

| Логин  | Пароль |
|--------|--------|
| `user` | `user` |

Остальные пользователи в базе нужны для заполнения «Топ-10», войти под ними нельзя (пароли случайные).

## Настройка

Конфигурация задаётся переменными окружения. Скопируйте пример и впишите свой ключ:

```bash
cp .env.example .env
```

Сгенерировать `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

| Переменная     | Назначение                              | По умолчанию                          |
|----------------|-----------------------------------------|---------------------------------------|
| `SECRET_KEY`   | Ключ подписи сессий Flask               | случайный при каждом запуске          |
| `DATABASE_URL` | Строка подключения SQLAlchemy           | `sqlite:///bank.db` (в `instance/`)   |
| `PORT`         | Порт при локальном запуске `python app.py` | `80`                               |

Если `SECRET_KEY` не задан, ключ генерируется заново при каждом старте, и все пользователи разлогиниваются.

## Запуск в Docker

### Docker Compose (рекомендуется)

```bash
docker compose up -d --build
```

Приложение будет доступно на http://localhost:8000. При первом запуске volume `gbank-data` заполняется демо-базой из образа, дальше данные сохраняются при пересоздании контейнера. Чтобы вернуть исходную базу, удалите volume: `docker compose down -v`.

Остановить:

```bash
docker compose down
```

### Без Compose

```bash
docker build -t gbank .
```

```bash
docker run -d --name gbank -p 8000:8000 --env-file .env -v gbank-data:/app/instance gbank
```

### Если сборка падает на `lookup registry-1.docker.io ... connection refused`

Виртуалка Docker не может резолвить DNS (часто из-за VPN). Для Colima перезапустите её с явными DNS-серверами:

```bash
colima stop && colima start --dns 8.8.8.8 --dns 1.1.1.1
```

## Локальный запуск без Docker

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

```bash
PORT=5000 python app.py
```

Приложение откроется на http://localhost:5000 (порт `80` по умолчанию требует прав root).

## Структура

```
app.py            маршруты и конфигурация
models.py         модели User и Transaction
forms.py          формы WTForms
templates/        Jinja2-шаблоны
static/           CSS и изображения
Dockerfile        образ приложения
docker-compose.yml
```
