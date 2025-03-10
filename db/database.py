from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tobot import config
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
#  У неё есть четыре столбца: id (первичный ключ), username, first_name и last_name.
class User(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer)
	username = Column(String)
	status = Column(String)
	level = Column(String)
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
	else:
		return None


# Функция для добавления вопросов в бд
def add_question(question_data):
	question = Question(**question_data)
	session.add(question)
	session.commit()


# Выбирает рандомно из таблицы question строки с полем id
def get_random_question(user_id, difficulty_level):
	# Получаем список вопросов, на которые пользователь уже ответил
	user = session.query(User).filter_by(user_id=user_id).first()

	answered_questions = user.count_answer.split() if user.count_answer else []

	# Определяем количество вопросов с указанным уровнем сложности
	total_questions = session.query(Question).filter(
		Question.difficulty_level == difficulty_level,
		Question.id.notin_(answered_questions)
	).count()

	if total_questions > 0:
		# Генерируем случайный индекс в диапазоне от 1 до общего количества вопросов
		random_index = random.randint(1, total_questions)

		# Получаем вопрос по индексу
		question = session.query(Question).filter(
			Question.difficulty_level == difficulty_level,
			Question.id.notin_(answered_questions),
			Question.id >= random_index
			).order_by(Question.id).first()

		return question
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


# Функция для перемешивания значений в формат строке
def shuffle_options(question):

	# Собираем все варианты ответов в список
	options = [
		question.answer_option_1,
		question.answer_option_2,
		question.answer_option_3,
		question.answer_option_4
	]

	# Перемешиваем варианты ответов
	random.shuffle(options)

	return options


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


def del_user_id(user_id):
	session.query(User).filter(User.user_id == user_id).delete()
	session.commit()





