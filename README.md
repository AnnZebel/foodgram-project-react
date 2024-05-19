# Foodrgam

 Продуктовый помощник - дипломный проект. Проект представляет собой онлайн-сервис, на котором пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное» и скачивать список продуктов, необходимых для приготовления блюд.

Проект реализован на `Django` и `DjangoRestFramework`. Доступ к данным реализован через API-интерфейс. Документация к API написана с использованием `Redoc`.

# Проект доступен по ссылкам:

```
http://foodgramblog.ddns.net/
```

# Логин и пароль администратора:
```
почта: ann@test.com
пароль: a1h7k88a
```

# Инструкция по запуску:
##### 1) Клонировать репозиторий и перейти в него в командной строке:
```
git@github.com:AnnZebel/foodgram-project-react.git
```
```
cd backend/
```
##### 2) Cоздать и активировать виртуальное окружение:
```
python3 -m venv env
```

```
source env/bin/activate
```

##### 3) Установить зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

##### 4) Запустить приложение в контейнерах:

из директории fixed-infra/
```
docker-compose up -d --build
```

## Шаблон наполнения env-файла

DB_ENGINE=django.db.backends.postgresql # указываем, что работаем с postgresql
DB_NAME=postgres # имя базы данных
POSTGRES_USER=postgres # логин для подключения к базе данных
POSTGRES_PASSWORD=postgres # пароль для подключения к БД
DB_HOST=db # название сервиса
DB_PORT=5432 # порт для подключения к БД 

## Стек технологий

Django==4.2.13
djangorestframework==3.15.1
djoser==2.1.0
django-cors-headers==3.13.0
psycopg2-binary==2.9.3
Pillow==9.0.0
django-filter==24.2
python-dotenv==1.0.1
gunicorn==20.1.0

