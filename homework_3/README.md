## API-сервис сокращения ссылок

## Запуск сервиса в Docker
```bash
# Забираем репозиторий
git clone https://github.com/your/repo.git
cd repo

# Запускаем сервис
docker compose up --build
```
Документация сервиса будет по адресу: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

## Основные роуты сервиса

### Авторизация 

- `POST /auth/register` — регистрация
- `POST /auth/jwt/login` — логин
- `GET /users/me` — получение данных о текущем пользователе

Login и Logout можно произвести через `Authorize` в правом верхнем углу Swagger

### Роуты для авторизованных пользователей
| Метод | Роут | Описание |
|-------|------|----------|
| `POST` | `/links/shorten` | Создать короткую ссылку (авторизированный юзер)
| `PATCH` | `/links/{short_code}` | Обновить URL (только автор ссылки)
| `DELETE` | `/links/{short_code}` | Удалить ссылку (только автор ссылки)
| `GET` | `links/user/all` | Получить список всех ссылок пользователя с их статусом

### Публичные роуты
| Метод | Роут | Описание |
|-------|------|----------|
| `POST` | `/links/public` | Создать короткую ссылку
| `GET` | `/{short_code}` | Редирект по ссылке
| `GET` | `/links/search?original_url=...` | Поиск ссылки по оригинальному URL
| `GET` | `/links/{short_code}/stats` | Получение статистики по ссылке

## Запись деплоя и демо сервиса

https://drive.google.com/file/d/1nA7RnD4x-gXJ2T_j8yq_w9b9Kv7SElR2/view?usp=drive_link

## Тесты
### Отчёт по покрытию сервиса тестами

[html_coverage_report](htmlcov/index.html)

![coverage](https://github.com/user-attachments/assets/09965a28-6efa-4e77-81d6-01b1e9d724a1)

### Нагрузочное тестирование (Locust)
[locust_report](tests/Locust_report.html)


![locust](https://github.com/user-attachments/assets/2bf12e2a-4560-4334-9ca1-28c3744d3838)
