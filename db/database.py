from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import config
import random

#  Подключение к базе данных
#  Здесь создаётся движок для подключения к базе данных SQLite, используя путь из переменной config.DB_PATH.
#  Это гибкий подход, позволяющий настраивать путь к базе данных извне (например, через конфигурационный файл).
Base = declarative_base()
db_path = config.DB_PATH

# Создаем движок для подключения к базе данных
engine = create_engine(f'sqlite:///{db_path}')
#  Создание сессии.
#  Создается фабрика сессий и экземпляр сессии, который будет использоваться для операций с базой данных.
Session = sessionmaker(bind=engine)
session = Session()


#  Определение модели таблицы.
#  Определяется класс User, который соответствует таблице users в базе данных.
#  У неё есть семь полей
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    username = Column(String)
    status = Column(String)
    level = Column(Integer)
    total = Column(Integer)
    count_answer = Column(String)


# Определение модели для таблицы questions
class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    question = Column(String)
    answer = Column(String)
    answer_option_1 = Column(String)
    answer_option_2 = Column(String)
    answer_option_3 = Column(String)
    answer_option_4 = Column(String)
    correct_option = Column(Integer)
    difficulty_level = Column(Integer)


# Инициализация схемы базы данных
Base.metadata.create_all(engine)


#  Добавление нового пользователя.
#  Эта функция принимает словарь user_data с параметрами пользователя и добавляет новую запись в таблицу users.
def add_user(user_data):
    user = User(**user_data)
    session.add(user)
    session.commit()


def next_level(user_id):
    """
    Функция стирает поле count_answer и увеличивает значение поля level на 1.
    """
    user = session.query(User).filter_by(user_id=user_id).first()
    # Обнуляем поле count_answer
    user.count_answer = None
    # Увеличиваем значение поля level на 1
    user.level = user.level + 1
    session.commit()


#  Получение всех пользователей.
#  Эта функция возвращает список всех записей из таблицы users.
def get_all_users():
    return session.query(User).all()


def get_all_values(user_telegram_id):
    # Получаем запись из базы данных по user_id
    user = session.query(User).filter_by(user_id=user_telegram_id).first()

    # Если запись найдена, возвращаем все поля в виде словаря
    if user:
        return {
            'id': user.id,
            'user_id': user.user_id,
            'username': user.username,
            'status': user.status,
            'level': user.level,
            'total': user.total,
            'count_answer': user.count_answer
        }
    else:
        return None  # Или другое значение, если запись не найдена


def get_values_answer(id_q):
    # Если запись найдена, возвращаем все поля в виде словаря
    result = session.query(Question).filter(Question.id == id_q).first()

    if result is not None:
        return result.answer

    return None


# Функция для добавления вопросов в бд
def add_question(question_data):
    question = Question(**question_data)
    session.add(question)
    session.commit()


# Функция удаляет из бд тестовый вопрос.
def del_question(id_quest):
    # Сначала проверяем наличие записи с данным id
    existing_question = session.query(Question).filter(Question.id == id_quest).first()

    if existing_question is not None:
        # Запись существует, удаляем её
        session.delete(existing_question)
        session.commit()
        return True

    return False


# Выбирает рандомно из таблицы question строки с полем id
def get_random_question(user_id, difficulty_level) -> (dict, None):
    """
    Данная функция предназначена для выбора случайного вопроса из базы данных,
    соответствующего определенному уровню сложности,
    при условии, что этот вопрос ранее не задавался данному пользователю.
    """
    # Получаем список вопросов, на которые пользователь уже ответил.
    user = session.query(User).filter_by(user_id=user_id).first()
    # Преобразовываем из строки в set.
    answered_quest = set(map(int, user.count_answer.split())) if user.count_answer else {}
    # Выбираем все значения id таблицы Question с значением поля difficulty_level.
    ids = session.query(Question.id).filter_by(difficulty_level=difficulty_level).all()
    # Преобразовываем из строки в set.
    set_ids = set(item[0] for item in ids)
    # Удаляем все элементы из set_ids которые есть в answered_quest и преобразовываем в список.
    res_id = list(set_ids.difference(answered_quest))

    # Если в списке есть хоть один элемент, условие срабатывает.
    if res_id:
        # Возвращаем случайный элемент из списка.
        rnd_id = random.choice(res_id)
        # Выбираем строку из таблицы Question с id == rnd_id.
        quest_id = session.query(Question).filter_by(id=rnd_id).first()

        # Создаём список с вариантами ответов.
        options = [
            quest_id.answer_option_1,
            quest_id.answer_option_2,
            quest_id.answer_option_3,
            quest_id.answer_option_4
        ]

        # Применяем функцию random.shuffle для случайной перестановки вариантов в списке.
        random.shuffle(options)

        quest_data = {
            'id': quest_id.id,
            'question': quest_id.question,
            'correct_answer': quest_id.answer_option_1,
            'correct_index': options.index(quest_id.answer_option_1) + 1,
            'options': options
        }

        return quest_data

    else:
        return None


# Функция для добавления в поле count_answer значение вопроса на который user ответил верно
def add_answer_to_count(user_id, id_q):
    # Получаем объект пользователя по user_id
    user = session.query(User).filter_by(user_id=user_id).first()

    # Получаем текущее значение поля count_answer
    current_value = user.count_answer or ""
    # Формируем новую строку, добавляя пробел между числами
    updated_value = f"{current_value}{id_q} "
    # Обновляем значение поля count_answer
    user.count_answer = updated_value
    # Сохраняем изменения в базе данных
    session.commit()


# Функция для записи в поле total значения 1
def update_total(user_id, value_to_add):
    # Получаем объект пользователя по user_id
    user = session.query(User).filter_by(user_id=user_id).first()

    if not user:
        return

    if value_to_add > 0:
        # Обновляем значение поля total
        new_total = user.total + value_to_add
        user.total = new_total
        # Сохраняем изменения в базе данных
        session.commit()
    elif value_to_add < 0:
        new_total = user.total - 1
        user.total = new_total
        # Сохраняем изменения в базе данных
        session.commit()


# Функция для проверки id пользователя
def find_user_id(value):
    # Создаем запрос для поиска строки с user_id равным value
    query = session.query(User.user_id).filter(User.user_id == value).scalar()
    # Возвращаем найденное значение или None, если ничего не найдено
    return int(query) if query is not None else None


# Функция проверяет у user_id поле status и если значение равно admin то возвращает user_id иначе None
def find_status(user_telegram_id):
    # Создаем запрос для поиска строки с user_telegram_id равным переданному значению
    query = session.query(User.user_id, User.status).filter(User.user_id == user_telegram_id)
    result = query.first()
    # # Если запись найдена и статус равен 'admin', возвращаем user_id

    if result and result[0] == user_telegram_id and result[1] == "admin":
        return result[0]
    else:
        return


def del_user_id(user_id, flag=False):
    """
    Функция принимает user_id с flag=False id телеграмм и удаляет строку в таблице по полю телеграм id,
    если передать в качестве user_id id строки с flag=True то функция удалит строку по id поля.
    """
    if flag:
        existing_user = session.query(User).filter(User.id == user_id).first()
        if existing_user is not None:
            # Запись существует, удаляем её
            session.delete(existing_user)
            session.commit()
            return True
        return False
    else:
        session.query(User).filter(User.user_id == user_id).delete()
    session.commit()





