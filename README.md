# Pyrogram Autoanswer Bot

Данное приложение позволяет автоматически отвечать пользователям, написавшим вам в Telegram. Возможные ответы хранятся в БД последовательно (по умолчанию их только три). 

Для каждого ответа указывается его текст и время отправки после предыдущего. Также возможно указать триггеры отмены отправки каждого конкретного ответа.

Перед запуском необходимо создать файл .env по примеру .env.example (значения TELEGRAM_API_ID и TELEGRAM_API_HASH можно получить на https://my.telegram.org/apps). При первом запуске будет необходимо авторизироваться в Telegram по номеру телефона.

В .env.example приведены дефолтные параметры для запуска с Docker.

## Установка и запуск
### Без Docker
Запустите PosgreSQL, укажите в .env необходимые параметры, после чего:
> pip install -r requirements.txt
>
> alembic upgrade heads
>
> python main.py

### С Docker
> pip install -r requirements.txt
>
> docker-compose build
>
> docker-compose up db
>
> alembic upgrade heads
>
> docker-compose up