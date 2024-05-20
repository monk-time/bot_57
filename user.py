from db import DataBase


class User:
    """Клиент бота.

    Содержит информацию о пользователе: имя, город, страну, название
    и смещение часового пояса. Может хранить идентификаторы земляков
    пользователя, а также флаг о том, что данные пользователя записаны в БД.
    """

    list_of_users = set()
    map_url = None
    map_europe_url = None
    num_of_users = 0

    def __init__(
        self,
        user_id,
        local_users=None,
        name=None,
        city=None,
        country=None,
        timezone=None,
        utc_offset=None,
        record=False,
        timer=None,
    ):
        self.id = user_id
        self.local_users = local_users
        self.name = name
        self.city = city
        self.country = country
        self.timezone = timezone
        self.utc_offset = utc_offset
        self.record = record
        self.timer = timer
        User.list_of_users.add(self)

    def __str__(self):
        return self.id

    def __repr__(self):
        return str(self.id)

    def load_from_db(self):
        """Загрузить информацию о сохраненном пользователе из БД."""
        db = DataBase(self.id)
        (
            self.name,
            self.city,
            self.country,
            self.timezone,
            self.utc_offset,
        ) = db.load_user()
        self.record = True
        active_timer = db.check_timer_exist()
        if active_timer:
            self.timer = active_timer[0]
        db.close()

    def save_user(self):
        """Сохранить информацию о пользователе в БД."""
        db = DataBase(self.id)
        if not db.check_user_exist() and self.timezone:
            db.create_user(
                self.name,
                self.city,
                self.country,
                self.timezone,
                self.utc_offset,
            )
            db.close()
            self.record = True
            return True
        db.close()
        return False

    def get_local_users(self):
        """Получить список земляков из того же города России или страны."""
        db = DataBase(self.id)
        if self.country == 'Россия':
            local_users = db.get_local_users(self.city)
        else:
            local_users = db.get_local_users_foreign(self.country)
        if self.id in local_users:
            local_users.remove(self.id)
        self.local_users = local_users
        db.close()
        return self.local_users


def activate_user(user_id):
    """Получить объект класса Пользователь.

    Если нужного объекта нет в памяти, создать его и
    загрузить связанные данные из БД.
    """
    user = next(
        (obj for obj in globals()['User'].list_of_users if obj.id == user_id),
        None,
    )
    if not user:
        user = User(user_id)
        db = DataBase(user_id)
        if db.check_user_exist():
            user.load_from_db()
        db.close()
    return user
