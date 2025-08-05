# Hero API (Django + PostgreSQL + Docker)

### Коротко
Мини-сервис с 2 эндпоинтами для работы с супергероями. ORM — Django, БД — PostgreSQL. Внешние данные: открытый датасет Akabab; при наличии непустого SUPERHERO\_API\_TOKEN можно использовать официальный superheroapi.com.

### Быстрый старт

```bash
docker compose down -v
docker compose up --build
```

Приложение поднимется на [http://localhost:8000/hero/](http://localhost:8000/hero/)
В docker-compose настроены Postgres 15 с healthcheck, ожидание БД (wait\_for\_db.py) и авто-миграции на старте.

Эндпоинты
```
POST /hero/
Тело JSON: { "name": "Batman" }
```
Поведение: ищет героя во внешнем источнике, сохраняет/обновляет запись и возвращает JSON. Если не найден, вернет ошибку.

```
GET /hero/
```
Параметры (все опциональные):
name — точное совпадение
intelligence, strength, speed, power — числовые фильтры:
точно: ?intelligence=100
больше/равно: ?intelligence\_\_gte=80
меньше/равно: ?intelligence\_\_lte=50

Примеры запросов
```
curl -X POST [http://localhost:8000/hero/](http://localhost:8000/hero/) -H "Content-Type: application/json" -d '{"name":"Batman"}'
curl "[http://localhost:8000/hero/](http://localhost:8000/hero/)"
curl "[http://localhost:8000/hero/?name=Batman](http://localhost:8000/hero/?name=Batman)"
curl "[http://localhost:8000/hero/?intelligence\_\_gte=80\&power\_\_lte=60](http://localhost:8000/hero/?intelligence__gte=80&power__lte=60)"
```

Переменные окружения (web)
```bash
DJANGO\_DEBUG — 1 или 0
DJANGO\_ALLOWED\_HOSTS — например \*
POSTGRES\_DB, POSTGRES\_USER, POSTGRES\_PASSWORD, POSTGRES\_HOST, POSTGRES\_PORT
SUPERHERO\_API\_TOKEN — опционально; если непустой, будет использован официальный API; иначе — Akabab all.json
```

Тесты
Локально (SQLite, отдельные настройки):
```bash
pytest
```

В контейнере (Postgres):
```bash
docker compose exec web pytest -q
```

Структура
```
hero\_api/
docker-compose.yml
Dockerfile
manage.py
wait\_for\_db.py
hero\_service/settings.py
hero\_service/settings\_test.py
hero\_service/urls.py
heroapp/models.py
heroapp/views.py
heroapp/urls.py
tests/test\_hero.py
```