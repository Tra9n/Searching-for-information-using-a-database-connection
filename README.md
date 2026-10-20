# Sky Project — отслеживание самолётов в воздушном пространстве
Курсовой проект: получение данных о самолётах, находящихся в воздухе, через открытые API и загрузка их в PostgreSQL.

# О проекте
Проект собирает данные о самолётах в воздушном пространстве выбранных стран с помощью:

Nominatim (OpenStreetMap) — для получения географических координат стран.

OpenSky Network — для получения данных о самолётах в заданной области.

Полученные данные сохраняются в PostgreSQL. Для работы с БД реализован класс DBManager с набором аналитических методов.

# Структура проекта
text
sky_project/
│
├── .env                          # Переменные окружения (не коммитится)
├── .gitignore
├── requirements.txt              # Зависимости
├── README.md
│
├── config.py                     # Настройки (чтение .env)
├── pytest.ini                    # Настройки pytest
│
├── sql/
│   └── schema.sql                # SQL-скрипт для создания таблиц
│
├── src/
│   ├── api/
│   │   ├── nominatim.py          # Работа с Nominatim API
│   │   └── opensky.py            # Работа с OpenSky API
│   ├── database/
│   │   ├── db_manager.py         # Класс DBManager
│   │   └── init_db.py            # Создание таблиц
│   └── utils/
│       └── logger.py             # Логирование
│
├── main.py                       # Точка входа
│
└── tests/
    ├── conftest.py               # Фикстуры
    ├── test_nominatim.py
    ├── test_opensky.py
    └── test_db_manager.py
# Требования
Python 3.10+

PostgreSQL 13+

Операционная система: Windows / Linux / macOS

# Установка
1. Клонируйте репозиторий
bash
git clone <url-репозитория>
cd sky_project
2. Создайте виртуальное окружение
Windows:

powershell
python -m venv .venv
.venv\Scripts\activate
Linux / macOS:

bash
python -m venv .venv
source .venv/bin/activate
3. Установите зависимости
bash
pip install -r requirements.txt
4. Настройте PostgreSQL
Создайте базу данных:

sql
CREATE DATABASE sky_db;
Убедитесь, что пользователь и пароль совпадают с теми, что вы укажете в .env.

5. Создайте файл .env в корне проекта
env
# Параметры БД
DB_NAME=sky_db
DB_USER=postgres
DB_PASSWORD=ваш_пароль
DB_HOST=localhost
DB_PORT=5432

# User-Agent для Nominatim (обязательно!)
NOMINATIM_USER_AGENT=SkyProject/1.0 (your_email@example.com)
Важно: Nominatim требует указывать реальный контактный email в User-Agent, иначе запросы блокируются.

Запуск
Основной сценарий
bash
python main.py
Скрипт:

Создаст таблицы (countries, aeroplanes), если их нет.

Получит bounding box для каждой страны из COUNTRIES (в config.py).

Запросит у OpenSky список самолётов в каждой области.

Сохранит данные в БД.

Выведет аналитику через DBManager.

Настройка списка стран
Отредактируйте COUNTRIES в config.py:

python
COUNTRIES = ["Germany", "France", "Italy", "Spain"]
Минимум — 4 страны (требование задания).

#️ Схема БД
sql
CREATE TABLE countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE aeroplanes (
    id SERIAL PRIMARY KEY,
    icao24 VARCHAR(10),
    callsign VARCHAR(20),
    origin_country VARCHAR(100),
    velocity REAL,
    country_id INTEGER REFERENCES countries(id)
);
Таблица	Поле	Описание
countries	id	Первичный ключ
name	Название страны
aeroplanes	icao24	Уникальный идентификатор самолёта
callsign	Позывной
origin_country	Страна регистрации
velocity	Скорость (м/с)
country_id	Ссылка на страну
# Класс DBManager
python
from src.database.db_manager import DBManager

db = DBManager()
Методы
Метод	Описание	Возвращает
get_countries_and_aeroplanes_count()	Список стран и количество самолётов	list[tuple[str, int]]
get_all_aeroplanes()	Список всех самолётов	list[tuple]
get_avg_speed()	Средняя скорость по всем самолётам	float
get_aeroplanes_with_higher_speed()	Самолёты со скоростью выше средней	list[tuple]
get_aeroplanes_with_keyword(keyword)	Поиск по позывному (регистронезависимо)	list[tuple]
Пример использования
python
from src.database.db_manager import DBManager

db = DBManager()

# Страны и количество самолётов
print(db.get_countries_and_aeroplanes_count())

# Средняя скорость
print(f"Средняя скорость: {db.get_avg_speed():.2f} м/с")

# Самолёты быстрее средней
for row in db.get_aeroplanes_with_higher_speed():
    print(row)

# Самолёты Air Canada
for row in db.get_aeroplanes_with_keyword("ACA"):
    print(row)

db.close()
# Тестирование
Установка dev-зависимостей
bash
pip install pytest pytest-mock pytest-cov
Запуск всех тестов
bash
pytest -v
Только unit-тесты (без БД)
Unit-тесты Nominatim и OpenSky используют моки и не требуют PostgreSQL:

bash
pytest -m "not integration" -v
Только интеграционные тесты
Требуют запущенный PostgreSQL:

bash
pytest -m integration -v
С покрытием
bash
pytest --cov=src --cov-report=term-missing
Что покрыто
Модуль	Сценарии
nominatim.py	Успешный ответ, страна не найдена, HTTP-ошибка
opensky.py	Успешный ответ, states=None, отсутствие ключа, HTTP-ошибка
db_manager.py	Подсчёт по странам (в т.ч. пустым), список самолётов, средняя скорость (в т.ч. на пустой БД), фильтр по скорости, поиск по ключу (регистр, частичное совпадение, отсутствие)
# Возможные проблемы
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc2
Это неверный пароль PostgreSQL — сообщение об ошибке возвращается в cp1251, а psycopg2 пытается прочитать его как UTF-8.

Решение: проверьте пароль в .env:

powershell
psql -U postgres -h localhost -c "SELECT 1;"
Если не подходит — сбросьте пароль:

В pg_hba.conf замените метод аутентификации для 127.0.0.1/32 на trust.

Перезапустите службу.

ALTER USER postgres WITH PASSWORD 'новый_пароль';

Верните scram-sha-256 в pg_hba.conf и снова перезапустите.

Connection refused
PostgreSQL не запущен:

powershell
Get-Service -Name postgresql*
Start-Service postgresql-x64-16
429 Too Many Requests от Nominatim
У Nominatim лимит — 1 запрос в секунду. В коде уже стоит time.sleep(1.2) между запросами. Не убирайте его.

403 Forbidden от OpenSky
OpenSky ограничивает анонимные запросы. При частых вызовах попробуйте зарегистрироваться на opensky-network.org и использовать Basic Auth.

# Источники данных
OpenSky Network REST API

Nominatim API

# Лицензия
Учебный проект. Используйте свободно в образовательных целях.

# Автор
Курсовой проект по работе с БД и внешними API.