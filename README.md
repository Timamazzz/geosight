# GeoSight

GeoSight - это проект для работы с данными OpenStreetMap. Описание будет добавлено позже.

## Первая установка

* Убедитесь, что на сервере или на вашем ПК установлены Docker и Docker Compose.
* Клонируйте проект по ссылке: https://github.com/Timamazzz/geosight.git.
* Создайте файл .env в корне проекта со следующими параметрами:
```properties
DB_NAME_OSM=osm-data
DB_USER_OSM=python-connector
DB_PASSWORD_OSM=python_connector_password

DB_NAME=ваш вариант
DB_USER=ваш вариант
DB_PASSWORD=ваш вариант

QUEUE_DEFAULT=ваш вариант
```
* Создайте файл .env в папке back со следующими параметрами:
```properties
SECRET_KEY=ваш вариант
DEBUG=(True/False)

DJANGO_ALLOWED_HOSTS=ваш вариант

CORS_ALLOW_ALL_ORIGINS=ваш вариант
CORS_ALLOW_CREDENTIALS=ваш вариант

CSRF_TRUSTED_ORIGINS=ваш вариант
CORS_ALLOWED_ORIGINS=ваш вариант

DB_ENGINE=django.contrib.gis.db.backends.postgis
DB_NAME=ваш вариант
DB_USER=ваш вариант
DB_PASSWORD=ваш вариант
DB_HOST=db
DB_PORT=5432

DB_NAME_OSM=osm-data
DB_USER_OSM=python-connector
DB_PASSWORD_OSM=python_connector_password
DB_PORT_OSM=5432

QUEUE_DEFAULT=ваш вариант
```
* Запустите контейнеры:
```shell
docker compose up --build -d
```
* Проверьте, что все контейнеры запущены и работают:
```shell
docker ps -a
```
* Зайдите в контейнер osm_db и загрузите дамп данных OpenStreetMap с игнорированием создателя:
```shell
pg_restore -U $DB_USER_OSM -d $DB_NAME_OSM --no-owner osm_backup.dump
```
* Если нужно, чтобы сайт работал на домене app.geosight.ru, убедитесь, что A-записи домена привязаны к серверу, на котором вы запускаете проект. Затем выполните команду в контейнере nginx:
```shell
certbot certonly --nginx -d app.geosight.ru
```
* Войдите в админ панель с логином admin и паролем admin. Не забудьте сменить пароль.

## Обновление проекта
Чтобы обновить проект, выполните следующие шаги:

* Внесите изменения в репозиторий и зафиксируйте их в ветке main.
* На сервере выполните команду для обновления кода:
```shell
git pull origin main
```
* Пересоберите и перезапустите контейнеры:
```shell
docker compose up --build -d
```