import re
from aiogram import Bot, types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from db.database import (add_user, get_all_users, add_question, get_random_question, update_total,
                         add_answer_to_count, find_user_id, get_all_values, del_user_id, del_question,
                         get_values_answer, next_level)
from keyboards.keybord import kb, kb_nc, kb_r, main_kb, kb_ap, kb_prof, kb_prof2, kb_next
import logging

from config import API_TOKEN


router = Router()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)


# Определяем набор состояний для reg
class RegUser(StatesGroup):
    reg_username = State()


# Определяем набор состояний для удаления пользователя
class DelUser(StatesGroup):
    del_user_id = State()


# Определяем набор состояний для adduser
class AddUser(StatesGroup):
    wait_username = State()
    wait_status = State()
    wait_level = State()


# Определяем набор состояний для addtest
class AddTest(StatesGroup):
    question = State()
    answer = State()
    answer_option_1 = State()
    answer_option_2 = State()
    answer_option_3 = State()
    answer_option_4 = State()
    correct_option = State()
    difficulty_level = State()


# Определяем набор состояний для check_answer (ожидание правильного ответа)
class CheckAnswer(StatesGroup):
    check_answer = State()
    hand_over = State()


# Определяем набор состояний для удаления пользователя
class DelTest(StatesGroup):
    del_test_id = State()


# USER ================================================================================================
# Регистрация
# Слушает кнопку reply_markup=kb_reg
@router.callback_query(F.data == 'answer_reg')
async def answer_reg(query: CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    value = find_user_id(user_id)
    if user_id != value:
        await query.message.answer("Введите ваше имя: ")
        await state.set_state(RegUser.reg_username)
    else:
        await query.message.answer("Tobot видит что вы уже зарегистрированы.")


@router.message(RegUser.reg_username)
async def answer_reg_state2(message: types.Message, state: FSMContext):
    if message.text.startswith('/'):
        # Сбрасываем состояние и отвечаем пользователю
        await state.clear()
        await message.answer("Похоже, вы ввели команду. Попробуйте ещё раз.    /start")
    else:
        # Сохраняем данные и продолжаем регистрацию
        await state.update_data(user_id=message.from_user.id, username=message.text, status="user", level="1",
                                total="0")
        user_data = await state.get_data()
        add_user(user_data)
        kb_menu = main_kb(message.from_user.id)
        await message.answer("Вы зарегистрированы!", reply_markup=kb_menu)
        await state.clear()


# Проверить свой id
@router.message(Command('id'))
async def id_command(message: Message):
    await message.answer(f"Ваш ID: {message.from_user.id}")


@router.message(Command('start'))
async def menu(message: Message, state: FSMContext):
    await state.clear()
    kb_menu = main_kb(message.from_user.id)
    user_id = message.from_user.id
    admin = find_user_id(user_id)
    if user_id != admin:
        # Приветственное сообщение с клавиатурой
        await message.answer(f'Добро пожаловать! Меня зовут Tobot.\n'
                             f'Я задаю вам вопрос, вы выбираете один ответ '
                             f'из четырёх вариантов. Тема QA-тестирование.\n'
                             f'Подробнее по кнопке Инфо', reply_markup=kb_menu)
    else:
        await message.answer(f'Tobot ждёт ваших действий...', reply_markup=kb_menu)


@router.callback_query(F.data == 'next_level')
async def next_l(query: CallbackQuery):
    user_id = query.from_user.id
    next_level(user_id)
    await query.message.edit_reply_markup(reply_markup=main_kb(user_id))


@router.callback_query(F.data == 'start_test')
async def start_test(query: CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    user = get_all_values(user_id)
    userid_bd = user.get('user_id')
    user_level = user.get('level')

    if user_id == userid_bd:
        dct_quest = get_random_question(user_id, user_level)

        if dct_quest is None:
            # Обработка ситуации, когда больше нет доступных вопросов
            await query.message.answer("К сожалению, все вопросы на данном уровне сложности закончились.\n"
                                       "Вам необходимо перейти на следующий уровень.", reply_markup=kb_next)
            return  # Прерывание функции, чтобы избежать дальнейших действий когда вопросы закончилис

        await state.update_data(id_q=dct_quest['id'],
                                correct_answer=dct_quest['correct_answer'],
                                correct_id=dct_quest['correct_index'],
                                options=dct_quest['options'],
                                user=user_id)

        await query.message.answer(f'\nВопрос {dct_quest['id']}: {dct_quest['question']}\n\n'
                                   f'Вариант 1: {dct_quest['options'][0]}\n'
                                   f'Вариант 2: {dct_quest['options'][1]}\n'
                                   f'Вариант 3: {dct_quest['options'][2]}\n'
                                   f'Вариант 4: {dct_quest['options'][3]}\n', reply_markup=kb)

        await state.set_state(CheckAnswer.check_answer)

    else:
        await query.message.answer("Зарегистрируйтесь")


# Обработчик нажатия кнопок button
# .startswith('answer')`: Проверяет, начинается ли эта строка с указанного текста ("answer").
@router.callback_query(CheckAnswer.check_answer, F.data.startswith('answer'))
async def answer_check1(query: CallbackQuery, state: FSMContext):
    button_index = int(query.data.split(':')[1])  # Извлекаем индекс варианта ответа из callback_data

    await state.update_data(answer_index=button_index)
    user_data = await state.get_data()  # Получаем данные из состояния
    user = user_data['user']
    id_q = user_data['id_q']

    if user_data['options'][button_index] == user_data['correct_answer']:
        await query.message.answer(f'Правильно! Вы получаете +1 балл /start', reply_markup=kb_nc)
        update_total(user, 1)
        add_answer_to_count(user, id_q)
    else:
        await query.message.answer(f'Неправильно! -1 балл. /start', reply_markup=kb_r)
        update_total(user, -1)
    await state.set_state(CheckAnswer.hand_over)


@router.callback_query(CheckAnswer.hand_over, F.data == 'answer_read')
async def answer_read(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data_full = get_values_answer(data['id_q'])  # Достаём ответ из бд с помощью функции get_values_answer
    data_num = data['correct_id']
    data_answer = data['correct_answer']
    # Очистка текста от лишних пробелов и спецсимволов
    data_answer = re.sub(r'\s+', ' ', data_answer.strip())
    data_full = re.sub(r'\s+', ' ', data_full.strip())
    await query.message.answer(f'Правильный вариант {data_num}:\n{data_answer}\n\nОпределение вопроса:\n{data_full}')


@router.callback_query(F.data == 'answer_prof')
async def answer_prof(query: CallbackQuery):
    user_id = query.from_user.id
    data = get_all_values(user_id)
    if data:
        await query.message.answer(f"ID пользователя: {data['id']}\n"
                                   f"Имя пользователя: {data['username']}\n"
                                   f"Кол-во балов: {data['total']}\n"
                                   f"Уровень знаний: {data['level']}\n"
                                   f"Правильных ответов: {data['total']}\n", reply_markup=kb_prof)
    else:
        await query.message.answer("Зарегистрируйтесь.")


@router.callback_query(F.data == 'del_user')
async def answer_prof(query: CallbackQuery):
    await query.message.answer("Статистика и профиль будут безвозвратно удалены! Продолжить?", reply_markup=kb_prof2)


@router.callback_query(F.data == 'del_user_next')
async def answer_prof(query: CallbackQuery):
    user_id = query.from_user.id
    del_user_id(user_id)
    await query.message.answer("Учётная запись удалена!")


# Обработчики команд info
@router.callback_query(F.data == 'answer_info')
async def info(query: CallbackQuery):
    await query.message.answer(f'Tobot — это бот, созданный специально для тех, кто хочет '
                               f'углубить свои знания в области тестирования программного '
                               f'обеспечения. Его основной функционал заключается в '
                               f'поэтапной выдаче вопросов, направленных на проверку ваших '
                               f'знаний в сфере QA. Бот запоминает вопросы на которые были '
                               f'даны правильные ответы и задаёт только те на которые '
                               f'вы не отвечали или ответили не верно.\n\n'
                               f'Что вас ждёт?\n\n'
                               f'- Богатая база вопросов. Все задания отобраны из книг и курсов '
                               f'по подготовке тестировщиков и инженеров по автоматизации '
                               f'тестирования на Python.\n'
                               f'- Уровневая система. Вопросы подбираются в зависимости от '
                               f'вашего текущего уровня.\n'
                               f'- Накопление баллов. За каждый верный ответ вы получаете '
                               f'очки, которые отражают вашу статистику. Ответив правильно '
                               f'на все вопросы данного уровня, вы переходите на новый уровень, где '
                               f'ждут ещё более интересные и сложные задачи.\n'
                               f'- Элемент неожиданности. Каждый раз вопросы генерируются '
                               f'случайным образом.')


@router.callback_query(F.data == 'answer_admin_panel')
async def admin_panel_command(query: CallbackQuery):
    await query.message.answer(f'Tobot слушает и повинуется!', reply_markup=kb_ap)


# ADMIN ================================================================================================
# Прочитать всех пользователей из базы данных
@router.callback_query(F.data == 'read_user')
async def read_command(query: CallbackQuery):
    users = get_all_users()
    output_message = ""
    for user in users:
        output_message += f"ID: {user.id}, Name: {user.username}, Status: {user.status}, Level: {user.level}\n"
    await query.message.answer(output_message)


# Удалить user=================================================================================================
@router.callback_query(F.data == 'delete_user')
async def del_command(query: CallbackQuery, state: FSMContext):
    await query.message.answer("input_id: ")
    await state.set_state(DelUser.del_user_id)


@router.message(DelUser.del_user_id)
async def del2_command(message: types.Message, state: FSMContext):
    await state.update_data(userid=message.text)
    user_id = await state.get_data()
    res = del_user_id(user_id['userid'], flag=True)  # flag=True параметр для включения в функции удаления по id
    if res:
        await message.answer("Пользователь удалён!")
    else:
        await message.answer("Пользователя с таким id не существует!")
    await state.clear()


# ADD_QUEST ================================================================================================
# Создать новый тестовый вопрос
@router.callback_query(F.data == 'add_test')
async def start_add_test(query: CallbackQuery, state: FSMContext):
    await query.message.answer("Введите тестовый вопрос:")
    await state.set_state(AddTest.question)


@router.message(AddTest.question)
async def process_question(message: types.Message, state: FSMContext):
    await state.update_data(question=message.text)
    await message.answer("Введите развёрнутый ответ:")
    await state.set_state(AddTest.answer)


@router.message(AddTest.answer)
async def process_answer(message: types.Message, state: FSMContext):
    await state.update_data(answer=message.text)
    await message.answer("Введите правильный вариант ответа 1:")
    await state.set_state(AddTest.answer_option_1)


# Добавление варианта ответа 1
@router.message(AddTest.answer_option_1)
async def process_answer_option_1(message: types.Message, state: FSMContext):
    await state.update_data(answer_option_1=message.text)
    await message.answer("Введите ложный вариант ответа 2:")
    await state.set_state(AddTest.answer_option_2)


# Добавление варианта ответа 2
@router.message(AddTest.answer_option_2)
async def process_answer_option_2(message: types.Message, state: FSMContext):
    await state.update_data(answer_option_2=message.text)
    await message.answer("Введите ложный вариант ответа 3:")
    await state.set_state(AddTest.answer_option_3)


# Добавление варианта ответа 3
@router.message(AddTest.answer_option_3)
async def process_answer_option_3(message: types.Message, state: FSMContext):
    await state.update_data(answer_option_3=message.text)
    await message.answer("Введите ложный вариант ответа 4:")
    await state.set_state(AddTest.answer_option_4)


# Добавление варианта ответа 4
@router.message(AddTest.answer_option_4)
async def process_answer_option_4(message: types.Message, state: FSMContext):
    await state.update_data(answer_option_4=message.text)
    await message.answer("Введите номер правильного варианта ответа:")
    await state.set_state(AddTest.correct_option)


# Добавление номера правильного ответа
@router.message(AddTest.correct_option)
async def process_answer(message: types.Message, state: FSMContext):
    await state.update_data(correct_option=message.text)
    await message.answer("Введите номер уровня сложности вопроса:")
    await state.set_state(AddTest.difficulty_level)


# Добавление вопроса в бд
@router.message(AddTest.difficulty_level)
async def process_save_answer(message: types.Message, state: FSMContext):
    await state.update_data(difficulty_level=message.text)
    test_data = await state.get_data()  # Собираем все данные из контекста состояния
    add_question(test_data)  # Передаем собранные данные в функцию add_add_question
    await message.answer("Данные успешно добавлены!")
    await state.clear()


# DEL_QUEST ================================================================================================
@router.callback_query(F.data == 'delete_test')
async def del_test(query: CallbackQuery, state: FSMContext):
    await query.message.answer("Введите id вопроса:")
    await state.set_state(DelTest.del_test_id)


@router.message(DelTest.del_test_id)
async def del_test2(message: types.Message, state: FSMContext):
    await state.update_data(del_test_id=message.text)
    test_id = await state.get_data()
    res = del_question(test_id['del_test_id'])
    if res:
        await message.answer("Тестовый вопрос удалён!")
    else:
        await message.answer("Тестового вопроса с таким id не существует!")
    await state.clear()

