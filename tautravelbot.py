import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
import json
import os

# Создаем диспетчер
dp = Dispatcher()

# Константы

CHAT_ID = "-1002530782917"  # ID чата администраторов
ADMIN_IDS = [686385290, 648034216, 1096741599]  # Список ID администраторов, замените на реальные

# Хранилище вопросов пользователей
user_questions = {}


# Функция для сохранения вопросов в файл
def save_questions():
    with open('user_questions.json', 'w', encoding='utf-8') as f:
        json.dump(user_questions, f, ensure_ascii=False)


# Функция для загрузки вопросов из файла
def load_questions():
    if os.path.exists('user_questions.json'):
        with open('user_questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


@dp.message(Command('start'))
async def start_command(message: types.Message) -> None:
    kb = [
        [types.InlineKeyboardButton(text='Что такое TauTravel', callback_data='about')],
        [types.InlineKeyboardButton(text='FAQ', callback_data='faq')],
        [types.InlineKeyboardButton(text='Задать свой вопрос', callback_data='ask_question')],
        [types.InlineKeyboardButton(text='Оставить пожелания', callback_data='feedback')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer('Добро пожаловать в телеграм-бот TauTravel', reply_markup=keyboard)


@dp.message(Command('admin'))
async def admin_command(message: types.Message) -> None:
    # Проверяем, является ли пользователь администратором
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет прав администратора.")
        return

    kb = [
        [types.InlineKeyboardButton(text='Список вопросов', callback_data='admin_questions')],
        [types.InlineKeyboardButton(text='Список пожеланий', callback_data='admin_feedback')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer('Панель администратора TauTravel', reply_markup=keyboard)


@dp.message(Command('reply'))
async def reply_command(message: types.Message, command: CommandObject) -> None:
    # Проверяем, является ли пользователь администратором
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет прав администратора.")
        return

    # Проверяем аргументы команды
    if not command.args:
        await message.answer("Использование: /reply ID_вопроса Ваш ответ")
        return

    args = command.args.split(' ', 1)
    if len(args) < 2:
        await message.answer("Использование: /reply ID_вопроса Ваш ответ")
        return

    question_id = args[0]
    answer_text = args[1]

    # Проверяем существование вопроса
    if question_id not in user_questions:
        await message.answer(f"Вопрос с ID {question_id} не найден.")
        return

    question_data = user_questions[question_id]
    user_id = question_data['user_id']
    question_text = question_data['text']

    # Отправляем ответ пользователю
    try:
        await message.bot.send_message(
            chat_id=user_id,
            text=f"Ответ на ваш вопрос:\n\nВопрос: {question_text}\n\nОтвет: {answer_text}"
        )
        # Обновляем статус вопроса
        user_questions[question_id]['answered'] = True
        user_questions[question_id]['answer'] = answer_text
        save_questions()

        await message.answer(f"Ответ на вопрос {question_id} успешно отправлен пользователю.")
    except Exception as e:
        await message.answer(f"Ошибка при отправке ответа: {e}")


@dp.callback_query(F.data == "admin_questions")
async def admin_questions_callback(callback: types.CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("У вас нет прав администратора.")
        return

    # Фильтруем только вопросы (не пожелания)
    questions = {qid: q for qid, q in user_questions.items() if
                 q['type'] == 'question' and not q.get('answered', False)}

    if not questions:
        await callback.message.answer("Нет новых вопросов.")
        await callback.answer()
        return

    # Создаем сообщение со списком вопросов
    message_text = "📋 Список неотвеченных вопросов:\n\n"

    for qid, q in questions.items():
        message_text += f"ID: {qid}\n"
        message_text += f"От: {q['username']} ({q['user_id']})\n"
        message_text += f"Вопрос: {q['text']}\n"
        message_text += f"Дата: {q['date']}\n"
        message_text += "\nЧтобы ответить, используйте команду:\n"
        message_text += f"/reply {qid} Ваш ответ\n\n"
        message_text += "-------------------\n\n"

    await callback.message.answer(message_text)
    await callback.answer()


@dp.callback_query(F.data == "admin_feedback")
async def admin_feedback_callback(callback: types.CallbackQuery) -> None:
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("У вас нет прав администратора.")
        return

    # Фильтруем только пожелания
    feedback = {qid: q for qid, q in user_questions.items() if q['type'] == 'feedback'}

    if not feedback:
        await callback.message.answer("Нет пожеланий.")
        await callback.answer()
        return

    # Создаем сообщение со списком пожеланий
    message_text = "📋 Список пожеланий:\n\n"

    for qid, q in feedback.items():
        message_text += f"ID: {qid}\n"
        message_text += f"От: {q['username']} ({q['user_id']})\n"
        message_text += f"Пожелание: {q['text']}\n"
        message_text += f"Дата: {q['date']}\n"
        message_text += "-------------------\n\n"

    await callback.message.answer(message_text)
    await callback.answer()


@dp.callback_query(F.data == "about")
async def about_callback(callback: types.CallbackQuery) -> None:
    await callback.message.answer(
        "TauTravel — сообщество путешественников и социальная сеть для любителей активного отдыха и гор.")
    await callback.answer()


@dp.callback_query(F.data == "faq")
async def faq_callback(callback: types.CallbackQuery) -> None:
    kb = [
        [types.InlineKeyboardButton(text='Как присоединиться к походу?', callback_data='faq_join')],
        [types.InlineKeyboardButton(text='Что брать с собой?', callback_data='faq_gear')],
        [types.InlineKeyboardButton(text='Нужна ли физподготовка?', callback_data='faq_fitness')],
        [types.InlineKeyboardButton(text='Как оплатить тур?', callback_data='faq_payment')],
        [types.InlineKeyboardButton(text='Возврат денег', callback_data='faq_refund')],
        [types.InlineKeyboardButton(text='Как установить приложение?', callback_data='faq_app')],
        [types.InlineKeyboardButton(text='Назад в главное меню', callback_data='back_to_main')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await callback.message.answer('Выберите интересующий вас вопрос:', reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "faq_join")
async def faq_join_callback(callback: types.CallbackQuery) -> None:
    await callback.message.answer(
        "Чтобы присоединиться к походу, выберите тур на нашем сайте или в приложении, заполните анкету участника и внесите предоплату. После этого с вами свяжется организатор похода.")
    await callback.answer()


@dp.callback_query(F.data == "faq_gear")
async def faq_gear_callback(callback: types.CallbackQuery) -> None:
    await callback.message.answer(
        "Список необходимого снаряжения зависит от типа похода. После регистрации вы получите подробную инструкцию по экипировке. Базовый набор включает: рюкзак, спальник, туристический коврик, треккинговую обувь и одежду по сезону.")
    await callback.answer()


@dp.callback_query(F.data == "faq_fitness")
async def faq_fitness_callback(callback: types.CallbackQuery) -> None:
    await callback.message.answer(
        "Да, для большинства наших походов требуется базовая физическая подготовка. Уровень сложности указан в описании каждого маршрута. Для новичков мы рекомендуем начинать с однодневных походов или маршрутов лёгкой категории.")
    await callback.answer()


@dp.callback_query(F.data == "faq_payment")
async def faq_payment_callback(callback: types.CallbackQuery) -> None:
    await callback.message.answer(
        "Оплатить тур можно банковской картой через наш сайт или приложение. Также возможна оплата по QR-коду или банковским переводом. Для бронирования места достаточно внести предоплату в размере 30% от стоимости тура.")
    await callback.answer()


@dp.callback_query(F.data == "faq_refund")
async def faq_refund_callback(callback: types.CallbackQuery) -> None:
    await callback.message.answer(
        "При отмене участия в походе за 14 дней до старта возвращается 100% оплаты, за 7-13 дней - 50%. При отмене менее чем за 7 дней предоплата не возвращается. В случае отмены похода организаторами возвращается полная стоимость.")
    await callback.answer()


@dp.callback_query(F.data == "faq_app")
async def faq_app_callback(callback: types.CallbackQuery) -> None:
    await callback.message.answer(
        "Приложение TauTravel доступно в App Store и Google Play. Скачайте его, зарегистрируйтесь с помощью email или через социальные сети и получите доступ к каталогу туров, отзывам и личному кабинету.")
    await callback.answer()


@dp.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: types.CallbackQuery) -> None:
    await start_command(callback.message)
    await callback.answer()


@dp.callback_query(F.data == "ask_question")
async def ask_question_callback(callback: types.CallbackQuery) -> None:
    await callback.message.answer(
        "Пожалуйста, напишите ваш вопрос в следующем сообщении. Он будет перенаправлен нашим специалистам.")
    # Устанавливаем состояние пользователя для следующего сообщения
    dp.user_data[callback.from_user.id] = {"state": "waiting_for_question"}
    await callback.answer()


@dp.callback_query(F.data == "feedback")
async def feedback_callback(callback: types.CallbackQuery) -> None:
    await callback.message.answer(
        "Пожалуйста, напишите ваше пожелание или отзыв в следующем сообщении. Мы ценим ваше мнение!")
    # Устанавливаем состояние пользователя для следующего сообщения
    dp.user_data[callback.from_user.id] = {"state": "waiting_for_feedback"}
    await callback.answer()


@dp.message()
async def all_handler(message: types.Message) -> None:
    user_id = message.from_user.id

    # Проверяем состояние пользователя
    if user_id in dp.user_data:
        state = dp.user_data[user_id].get("state")

        if state == "waiting_for_question":
            # Генерируем уникальный ID для вопроса
            import time
            question_id = f"q{int(time.time())}"

            # Сохраняем вопрос
            user_questions[question_id] = {
                "user_id": user_id,
                "username": message.from_user.username or message.from_user.full_name,
                "text": message.text,
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "type": "question",
                "answered": False
            }
            save_questions()

            # Пересылаем вопрос в чат поддержки
            try:
                await message.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"Новый вопрос (ID: {question_id}):\n\n"
                         f"От: {message.from_user.full_name} (@{message.from_user.username})\n"
                         f"ID пользователя: {user_id}\n\n"
                         f"Вопрос: {message.text}\n\n"
                         f"Чтобы ответить, используйте команду:\n"
                         f"/reply {question_id} Ваш ответ"
                )
                await message.answer("Спасибо за ваш вопрос! Наши специалисты ответят вам в ближайшее время.")
            except Exception as e:
                await message.answer(
                    f"Извините, произошла ошибка при отправке вашего вопроса. Пожалуйста, попробуйте позже.")
                print(f"Error sending message to admin chat: {e}")

            # Сбрасываем состояние
            dp.user_data.pop(user_id)
            return

        elif state == "waiting_for_feedback":
            # Генерируем уникальный ID для пожелания
            import time
            feedback_id = f"f{int(time.time())}"

            # Сохраняем пожелание
            user_questions[feedback_id] = {
                "user_id": user_id,
                "username": message.from_user.username or message.from_user.full_name,
                "text": message.text,
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "type": "feedback"
            }
            save_questions()

            # Пересылаем пожелание в чат поддержки
            try:
                await message.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"Новое пожелание (ID: {feedback_id}):\n\n"
                         f"От: {message.from_user.full_name} (@{message.from_user.username})\n"
                         f"ID пользователя: {user_id}\n\n"
                         f"Пожелание: {message.text}"
                )
                await message.answer("Спасибо за ваш отзыв! Мы обязательно учтем ваше мнение.")
            except Exception as e:
                await message.answer(
                    f"Извините, произошла ошибка при отправке вашего пожелания. Пожалуйста, попробуйте позже.")
                print(f"Error sending message to admin chat: {e}")

            # Сбрасываем состояние
            dp.user_data.pop(user_id)
            return

    # Если нет особого состояния, отправляем стандартное сообщение
    kb = [
        [types.InlineKeyboardButton(text='Вернуться в меню', callback_data='back_to_main')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer("Я не понимаю этой команды. Пожалуйста, воспользуйтесь меню.", reply_markup=keyboard)


async def main() -> None:
    # Загружаем сохраненные вопросы
    global user_questions
    user_questions = load_questions()

    # Инициализация хранилища состояний пользователей
    dp.user_data = {}

    token = ""  # Замените на ваш токен бота
    bot = Bot(token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
