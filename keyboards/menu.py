# menu.py

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu():
    """
    Формирует главное меню из четырёх кнопок с помощью InlineKeyboardBuilder:
    - Получить конфигурацию
    - Мой профиль
    - Инструкция
    - Поддержка
    """
    builder = InlineKeyboardBuilder()

    # добавляем по одной кнопке в каждую строку
    builder.button(text="🔧 Получить конфигурацию", callback_data="get_config")
    builder.button(text="👤 Мой профиль", callback_data="my_profile")
    builder.button(text="📖 Инструкция", callback_data="instruction")
    builder.button(text="💬 Поддержка", callback_data="support")

    # разбиваем на 4 строки по 1 кнопке
    builder.adjust(1, 2, 1)

    return builder.as_markup()


def get_config_menu():
    """
    Меню «Получить конфигурацию» с пятью кнопками:
    - Тестовый конфиг
    - Платный на 1 месяц
    - Платный на 3 месяца
    - Платный на 6 месяцев
    - Платный на 12 месяцев
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="🧪 Тестовый конфиг", callback_data="trial")
    builder.button(text="📅 Платный 1 мес. - 250₽", callback_data="paid_config_1")
    builder.button(text="📅 Платный 3 мес. - 690₽", callback_data="paid_config_3")
    builder.button(text="📅 Платный 6 мес. - 1300₽", callback_data="paid_config_6")
    builder.button(text="📅 Платный 12 мес. - 2400₽", callback_data="paid_config_12")
    builder.button(text="↩️ Назад", callback_data="back")
    # По одной кнопке в строке
    builder.adjust(1)
    return builder.as_markup()


def get_profile_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Получить конфиг", callback_data="send_config")
    builder.button(text="↩️ Назад", callback_data="back")
    builder.adjust(1, 1)
    return builder.as_markup()


def back_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="↩️ Назад", callback_data="back")
    return builder.as_markup()