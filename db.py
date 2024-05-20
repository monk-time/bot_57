import sqlite3


class DataBase:  # noqa: PLR0904
    """Класс работы с базой данных проекта.

    Объект класса привязывается к идентификатору каждого пользователя.
    """

    def __init__(self, user_id=None):
        self.connection = sqlite3.connect('db/cogorta.sqlite')
        self.cursor = self.connection.cursor()
        self.user_id = user_id

    def create_database(self):
        """Инициализировать базу данных."""
        with self.connection:
            self.cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    name TEXT,
                    city TEXT,
                    country TEXT,
                    timezone TEXT,
                    utc_offset INTEGER
                );
                CREATE TABLE IF NOT EXISTS timers(
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    sprint INTEGER,
                    start TEXT,
                    end TEXT,
                    total TEXT
                );
                CREATE TABLE IF NOT EXISTS reviews(
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    time TEXT,
                    key TEXT
                );
                """
            )
        return True

    def create_user(self, name, city, country, timezone, utc_offset):
        """Сохранить информацию о пользователе."""
        with self.connection:
            self.cursor.execute(
                """
                INSERT INTO users (
                    user_id, name, city, country, timezone, utc_offset)
                VALUES(?, ?, ?, ?, ?, ?);
                """,
                (self.user_id, name, city, country, timezone, utc_offset),
            )

    def load_user(self):
        """Загрузить информацию о сохраненном пользователе."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT name, city, country, timezone, utc_offset
                FROM users
                WHERE user_id = ?;
                """,
                (self.user_id,),
            )
        return self.cursor.fetchone()

    def get_local_users(self, city):
        """Получить список земляков пользователя из того же города."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE city = ?;
                """,
                (city,),
            )
        return [user[0] for user in self.cursor.fetchall()]

    def get_local_users_foreign(self, country):
        """Получить список земляков пользователя из той же страны."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE country = ?;
                """,
                (country,),
            )
        return [user[0] for user in self.cursor.fetchall()]

    def check_user_exist(self):
        """Проверить существование записи о пользователе с заданным ID в БД."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT EXISTS
                (SELECT * FROM users
                WHERE user_id = ?);
                """,
                (self.user_id,),
            )
        return self.cursor.fetchone()[0]

    def get_locations_ru(self):
        """Получить города всех пользователей из России."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT city, COUNT(user_id) AS people
                FROM users
                WHERE country = 'Россия'
                GROUP BY city
                ORDER BY people DESC;
                """
            )
        return self.cursor.fetchall()

    def get_locations_ino(self):
        """Получить страны всех пользователей за пределами России."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT country, COUNT(user_id) AS people
                FROM users
                WHERE country <> 'Россия'
                GROUP BY country
                ORDER BY people DESC;
                """
            )
        return self.cursor.fetchall()

    def get_timezones(self):
        """Получить информацию о часовых поясах всех пользователей."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT timezone, utc_offset, COUNT(user_id) AS people
                FROM users
                GROUP BY timezone
                ORDER BY people DESC;
                """
            )
        return self.cursor.fetchall()

    def start_timer(self, sprint):
        """Записать время старта таймера учебы."""
        with self.connection:
            self.cursor.execute(
                """
                INSERT INTO timers (user_id, sprint, start)
                VALUES(?, ?, datetime('now'));
                """,
                (self.user_id, sprint),
            )

    def end_timer(self):
        """Записать время остановки таймера учебы."""
        with self.connection:
            self.cursor.execute(
                """
                UPDATE timers
                SET end = datetime('now'),
                    total = (strftime('%s','now')-strftime('%s',start))
                WHERE user_id = ?
                AND end IS NULL;
                """,
                (self.user_id,),
            )

    def last_timer(self):
        """Получить последнюю запись таймера для конкретного пользователя."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT MAX(id)
                FROM timers
                WHERE user_id = ?;
                """,
                (self.user_id,),
            )
        return self.cursor.fetchone()

    def last_timer_duration(self, timer_id):
        """Получить информацию о сессии таймера с определенным ID."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT sprint, start,
                (total/3600) || ':' || strftime('%M:%S', total/86400.0)
                FROM timers
                WHERE id = ?;
                """,
                (timer_id,),
            )
        return self.cursor.fetchone()

    def check_timer_exist(self):
        """Проверить наличие запущенного таймера у пользователя."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT start
                FROM timers
                WHERE user_id = ?
                AND end IS NULL;
                """,
                (self.user_id,),
            )
        return self.cursor.fetchone()

    def check_all_active_timers(self):
        """Проверить наличие всех запущенных таймеров."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT user_id, start
                FROM timers
                WHERE end IS NULL;
                """
            )
        return self.cursor.fetchall()

    def sprint_time(self, sprint):
        """Cуммировать время потраченное на определенный спринт."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT (SUM(total)/3600) || ':' ||
                strftime('%M:%S', SUM(total)/86400.0)
                FROM timers
                WHERE sprint = ?
                AND user_id = ?;
                """,
                (sprint, self.user_id),
            )
        return self.cursor.fetchone()

    def all_sprints(self):
        """Статистика по времени, затраченному на прохождение спринтов."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT sprint,
                (SUM(total)/3600) || ':' ||
                strftime('%M:%S', SUM(total)/86400.0) AS time
                FROM timers
                WHERE user_id = ?
                GROUP BY sprint
                ORDER BY SUM(total) DESC;
                """,
                (self.user_id,),
            )
        return self.cursor.fetchall()

    def token_record(self, token):
        """Записать первичный токен к API Яндекс Практикума."""
        with self.connection:
            self.cursor.execute(
                """
                INSERT INTO reviews (user_id, time, key)
                VALUES(?, strftime('%s','now'), ?);
                """,
                (self.user_id, token),
            )

    def token_time_update(self, time):
        """Обновить временную метку последнего обращения к API."""
        with self.connection:
            self.cursor.execute(
                """
                UPDATE reviews
                SET time = ?
                WHERE user_id = ?;
                """,
                (time, self.user_id),
            )

    def token_exist(self):
        """Проверить наличие токена API, извлечь ключ и временную метку."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT time, key
                FROM reviews
                WHERE user_id = ?;
                """,
                (self.user_id,),
            )
        return self.cursor.fetchone()

    def all_active_tokens(self):
        """Вывести все активные токены API Яндекс Практикума."""
        with self.connection:
            self.cursor.execute(
                """
                SELECT user_id, time, key
                FROM reviews
                WHERE time IS NOT NULL;
                """
            )
        return self.cursor.fetchall()

    def close(self):
        """Закрыть соединение с базой данных."""
        self.connection.close()
