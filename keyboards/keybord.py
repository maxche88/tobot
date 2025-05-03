from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db.database import find_status


# Клавиатура после правильного ответа
kb_nc = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text='Следующий', callback_data='start_test')]]
)

# Клавиатура после не правильного ответа read
kb_r = InlineKeyboardMarkup(
    inline_keyboard=[[
                    InlineKeyboardButton(text='Следующий', callback_data='start_test'),
                    InlineKeyboardButton(text='Читать ответ', callback_data='answer_read')
                    ]])


# Клавиатура с вариантами ответов
kb = InlineKeyboardMarkup(
    inline_keyboard=[[
                    InlineKeyboardButton(text='Вариант 1', callback_data=f'answer:0'),
                    InlineKeyboardButton(text='Вариант 2', callback_data=f'answer:1')
                    ],
                    [
                    InlineKeyboardButton(text='Вариант 3', callback_data=f'answer:2'),
                    InlineKeyboardButton(text='Вариант 4', callback_data=f'answer:3')
                    ]]
)


# Клавиатура admin панели
kb_ap = InlineKeyboardMarkup(
    inline_keyboard=[
                    [InlineKeyboardButton(text='/read_user', callback_data='read_user')],
                    [InlineKeyboardButton(text='/delete_user', callback_data='delete_user')],
                    [InlineKeyboardButton(text='/add_test', callback_data='add_test')],
                    [InlineKeyboardButton(text='/delete_test', callback_data='delete_test')]
                    ]
)


# Клавиатура удалить пользователя
kb_prof = InlineKeyboardMarkup(
    inline_keyboard=[
                    [InlineKeyboardButton(text='Удалить', callback_data='del_user')]
                    ]
)


# Клавиатура подтверждения удаления пользователя
kb_prof2 = InlineKeyboardMarkup(
    inline_keyboard=[
                    [InlineKeyboardButton(text='Да', callback_data='del_user_next')],
                    [InlineKeyboardButton(text='Отмена', callback_data='answer_prof')]
                    ]
)


kb_next = InlineKeyboardMarkup(
    inline_keyboard=[
                    [InlineKeyboardButton(text='Перейти', callback_data='next_level')]
                    ]
)


def main_kb(user_telegram_id: int):
    """
    Функция возвращает клавиатуру пользователям, если id пользователя
    соответствует статусу admin то возвращает клавиатуру с дополнительной кнопкой
    admin_panel.
    """
    base_buttons = [
        [
            InlineKeyboardButton(text="📝 Начать тест", callback_data='start_test'),
            InlineKeyboardButton(text="👤 Мой профиль", callback_data='answer_prof')
        ],
        [
            InlineKeyboardButton(text="📝 Регистрация", callback_data='answer_reg'),
            InlineKeyboardButton(text="📚 ИНФО", callback_data='answer_info')
        ]
    ]

    # Проверяем, является ли пользователь администратором
    status = find_status(user_telegram_id)
    if user_telegram_id == status:
        # Добавляем дополнительную строку кнопок для администратора
        base_buttons.append([InlineKeyboardButton(text="⚙️ Админ панель", callback_data='answer_admin_panel')])

    # Создаём объект InlineKeyboardMarkup на основе подготовленных кнопок
    kb_menu = InlineKeyboardMarkup(inline_keyboard=base_buttons)

    return kb_menu

