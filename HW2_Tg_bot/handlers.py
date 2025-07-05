from aiogram.types import ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from states import ProfileStates, WorkoutStates
from aiogram.fsm.context import FSMContext
from aiogram import Router
import utils
from config import TEMP_TOKEN

router = Router()

# Данные пользователей
users = {}
users_data = {}

# Заготовленные типы тренировок
WORKOUT_TYPES = ["Кардио", "Силовая", "Йога", "Плавание"]

# Калории, сжигаемые за 1 минуту тренировки
CALORIES_PER_MINUTE = {"Кардио": 10, "Силовая": 8, "Йога": 4, "Плавание": 14}


# Дополнительная вода (мл), которую нужно выпить за каждую минуту тренировки
WATER_PER_MINUTE = {"Кардио": 12, "Силовая": 10, "Йога": 8, "Плавание": 15}


# Старт диалога
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply(
        "Добро пожаловать! Я ваш бот.\nВведите /set_profile, чтобы начать.")


# Установка профиля
@router.message(Command('set_profile'))
async def set_profile(message: Message, state: FSMContext):
    await state.set_state(ProfileStates.weight)
    await message.answer("Введите ваш вес (в кг):")


# Вес
@router.message(ProfileStates.weight)
async def get_weight(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer('Пожалуйста, введите число.')
        return
    await state.update_data(weight=int(message.text))
    await state.set_state(ProfileStates.height)
    await message.answer("Введите ваш рост (в см):")


# Рост
@router.message(ProfileStates.height)
async def get_height(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer('Пожалуйста, введите число.')
        return
    await state.update_data(height=int(message.text))
    await state.set_state(ProfileStates.age)
    await message.answer("Введите ваш возраст:")


# Возраст
@router.message(ProfileStates.age)
async def get_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer('Пожалуйста, введите число.')
        return
    await state.update_data(age=int(message.text))
    await state.set_state(ProfileStates.activity)
    await message.answer("Сколько минут активности за день у вас было?")


# Активности
@router.message(ProfileStates.activity)
async def get_activity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число.")
        return
    await state.update_data(activity=int(message.text))
    await state.set_state(ProfileStates.city)
    await message.answer("В каком городе вы находитесь? (Укажите на английском)")


# Город
@router.message(ProfileStates.city)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(ProfileStates.calorie_goal_input)
    await message.answer("У вас есть цель по количеству калорий?\n"
                         "Если да, укажите её (в ккал). Если нет, просто введите 'нет'.")


# Норма калорий и воды
@router.message(ProfileStates.calorie_goal_input)
async def get_calorie_input(message: Message, state: FSMContext):
    user_answer = message.text.strip().lower()
    user_data = await state.get_data()
    # Если нет цели по калориям, то расчёт по формуле
    if user_answer == 'нет':
        calorie_goal = utils.calculate_calories(
            weight=user_data['weight'],
            height=user_data['height'],
            age=user_data['age'],
            activity=user_data['activity'])
        await state.update_data(calorie_goal=calorie_goal)

    # Если указана цель по калориям
    elif user_answer.isdigit():
        calorie_goal = int(user_answer)
        await state.update_data(calorie_goal=calorie_goal)

    # Обработка некорректного ввода
    else:
        await message.answer("Пожалуйста, введите число или 'нет'.")
        return

    # Теперь расчёт нормы воды
    water_goal = utils.calculate_water(
        weight=user_data['weight'],
        activity=user_data['activity'])

    # Получаем текущую температуру в городе для доп расчёта воды
    current_temp = utils.get_temp(user_data['city'], TEMP_TOKEN)
    if current_temp > 25:
        water_goal += 500
    await state.update_data(water_goal=water_goal)

    # Получаем все данные
    user_data = await state.get_data()

    user_id = message.from_user.id
    users_data[user_id] = {
        "weight": user_data['weight'],
        "height": user_data['height'],
        "age": user_data['age'],
        "activity": user_data['activity'],
        "city": user_data['city'],
        "calorie_goal": calorie_goal,
        "water_goal": water_goal}

    await message.answer(
        f"Ваш профиль сохранен:\n"
        f"Вес: {user_data['weight']} кг\n"
        f"Рост: {user_data['height']} см\n"
        f"Возраст: {user_data['age']} лет\n"
        f"Активность за день: {user_data['activity']} минут\n"
        f"Город: {user_data['city']}\n"
        f"Цель по воде: {water_goal} мл\n"
        f"Цель по калориям: {calorie_goal} ккал",
        reply_markup=ReplyKeyboardRemove())
    await state.clear()


# Команда для просмотра текущего профиля
@router.message(Command('show_profile'))
async def show_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    # Проверка, существует ли профиль
    if user_id not in users_data:
        await message.answer("Ваш профиль не найден. Сначала настройте профиль с помощью /set_profile.")
        return

    user_profile = users_data[user_id]
    # Базовые данные профиля
    profile_info = (
        f"Ваш профиль\n\n"
        f"Вес: {user_profile.get('weight', 'не указан')} кг\n"
        f"Рост: {user_profile.get('height', 'не указан')} см\n"
        f"Возраст: {user_profile.get('age', 'не указан')} лет\n"
        f"Активность за день: {user_profile.get('activity', 'не указана')} мин/день\n"
        f"Город: {user_profile.get('city', 'не указан')}\n"
        f"Цель по калориям: {user_profile.get('calorie_goal', 'не указана')} ккал\n"
        f"Цель по воде: {user_profile.get('water_goal', 'не указана')} мл\n")

    # Залогированные данные
    logged_info = (
        f"\nЗалогированные показатели:\n"
        f"Выпито воды: {user_profile.get('logged_water', 0)} мл\n"
        f"Потреблено калорий: {user_profile.get('logged_calories', 0)} ккал\n"
        f"Сожжено калорий (тренировки): {user_profile.get('burned_calories', 0)} ккал\n")

    # Отправляем пользователю
    await message.answer(profile_info + logged_info)


# Команда для логирования воды
@router.message(Command('log_water'))
async def log_water(message: Message, state: FSMContext):
    user_id = message.from_user.id
    # Проверка, существует ли профиль
    if user_id not in users_data or "water_goal" not in users_data[user_id]:
        await message.answer("Ваш профиль не найден. Сначала настройте профиль с помощью /set_profile.")
        return

    await state.set_state(ProfileStates.logged_water)
    await message.answer("Сколько воды (в мл) вы выпили за день?")


# Обработчик логирования воды
@router.message(ProfileStates.logged_water)
async def handle_logged_water(message: Message, state: FSMContext):
    user_answer = message.text.strip().lower()
    if user_answer.isdigit():
        # Расчёт сколько осталось до выполнения нормы
        logged_water = int(user_answer)
        await state.update_data(logged_water=logged_water)

        # Сохраняем количество выпитой воды
        user_id = message.from_user.id
        if "logged_water" not in users_data[user_id]:
            users_data[user_id]["logged_water"] = 0  # дефолтное значение
        users_data[user_id]["logged_water"] += logged_water
        logged_water = users_data[user_id]["logged_water"]

        # Сколько воды осталось выпить
        water_goal = users_data[user_id]["water_goal"]
        water_left = round(water_goal - logged_water)

        if water_left <= 0:
            await message.answer(f"Вы выпили {logged_water} мл воды.\n"
                                 f"Вы выпили дневную норму воды, так держать!")
        else:
            await message.answer(f"Вы выпили {logged_water} мл воды.\n"
                                 f"До выполнения нормы осталось выпить {water_left} мл.")
        await state.clear()
    else:
        await message.answer("Пожалуйста, введите число.")


# Команда для логирования еды
@router.message(Command('log_food'))
async def log_food(message: Message, state: FSMContext):
    user_id = message.from_user.id
    # Проверка, существует ли профиль
    if user_id not in users_data:
        await message.answer("Ваш профиль не найден. Сначала настройте профиль с помощью /set_profile.")
        return

    await state.set_state(ProfileStates.logged_calories)
    await message.answer("Введите продукт и сколько грамм вы съели для записи калорий."
                         ' Пример: banana 150')


# Обработчик логирования еды
@router.message(ProfileStates.logged_calories)
async def handle_logged_calories(message: Message, state: FSMContext):
    user_answer = message.text.strip().lower().split(' ')
    user_clrs = user_answer[-1]
    user_food = user_answer[0]
    if user_clrs.isdigit():
        # Указываем дефолтное значение калорий, если api отвалиться (такое было при локальном тесте)
        food_info = utils.get_food_info(user_food)
        if food_info is None:
            food_clrs = {'calories': 250}.get('calories')
        else:
            food_clrs = food_info.get('calories')

        # Сохраняем количество калорий
        logged_calories = (int(user_clrs) * food_clrs) / 100
        await state.update_data(logged_calories=logged_calories)

        user_id = message.from_user.id
        if "logged_calories" not in users_data[user_id]:
            users_data[user_id]["logged_calories"] = 0  # дефолтное значение
        users_data[user_id]["logged_calories"] += logged_calories

        await message.answer(f"{user_food} - {food_clrs} ккал на 100 г.\n"
                             f"Записано {logged_calories} ккал.")
        await state.clear()
    else:
        await message.answer("Пожалуйста, введите число.")


# Команда для логирования тренировок
@router.message(Command('log_workout'))
async def log_workout(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in users_data:
        await message.answer("Ваш профиль не найден. Сначала настройте профиль с помощью /set_profile.")
        return

    # Инлайн-клавиатура с типами тренировок
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=workout, callback_data=f"workout_type:{workout}")]
        for workout in WORKOUT_TYPES])

    await message.answer("Выберите тип тренировки:", reply_markup=keyboard)
    await state.set_state(WorkoutStates.choose_type)


# Обработчик выбора типа тренировки
@router.callback_query(lambda c: c.data.startswith("workout_type"))
async def choose_type(callback_query: CallbackQuery, state: FSMContext):
    workout_type = callback_query.data.split(":")[1]
    await state.update_data(workout_type=workout_type)
    await callback_query.message.edit_text(f"Вы выбрали: {workout_type}")

    # Инлайн-клавиатура выбора длительности тренировки
    durations = ["15 минут", "30 минут", "45 минут", "60 минут", "90 минут"]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=duration, callback_data=f"workout_duration:{duration}")]
        for duration in durations])
    await callback_query.message.answer("Теперь выберите длительность тренировки:", reply_markup=keyboard)
    await state.set_state(WorkoutStates.choose_duration)


# Обработчик выбора длительности тренировки
@router.callback_query(lambda c: c.data.startswith("workout_duration"))
async def choose_duration(callback_query: CallbackQuery, state: FSMContext):
    duration = callback_query.data.split(":")[1]
    duration_mins = int(duration.split()[0])  # длительность тренировки в минутах
    user_data = await state.get_data()
    workout_type = user_data.get("workout_type")

    # Расчёт и сохранение сожённых калорий и дополнительной воды
    burned_calories = CALORIES_PER_MINUTE.get(workout_type, 0) * duration_mins
    extra_water = WATER_PER_MINUTE.get(workout_type, 0) * duration_mins
    await state.update_data(burned_calories=burned_calories)

    user_id = callback_query.from_user.id
    if "burned_calories" not in users_data[user_id]:
        users_data[user_id]["burned_calories"] = 0  # дефолтное значение
    users_data[user_id]["burned_calories"] += burned_calories
    users_data[user_id]["water_goal"] += extra_water

    # Данные по калориям для рекомендации по итогам тренировки
    calorie_goal = users_data[user_id]["calorie_goal"]
    logged_calories = users_data[user_id]['logged_calories']
    balance_calories = round(logged_calories - burned_calories)

    # Формирование текста ответа
    result_text = (
        f"Вы записали тренировку: {workout_type}, длительность: {duration}.\n"
        f"Сожжено калорий: {burned_calories} ккал.\n"
        f"Рекомендуется выпить дополнительно воды: {extra_water} мл.\n")

    # Рекомендации
    burned_calories = users_data[user_id]["burned_calories"]
    balance_calories = round(logged_calories - burned_calories)
    if balance_calories <= calorie_goal:
        result_text += "Вы находитесь в балансе по калориям, так держать!"
    else:
        result_text += (
            f"Для баланса по калориям необходимо сжечь не менее {balance_calories - calorie_goal} ккал.\n"
            "Наиболее подходящими тренировками для этого будут Плавание и Кардио.")

    # Отправка сообщения и завершение состояния
    await callback_query.message.edit_text(result_text)
    await state.clear()


# Команда для проверки прогресса
@router.message(Command('check_progress'))
async def check_progress(message: Message, state: FSMContext):
    user_id = message.from_user.id
    # Проверка, существует ли профиль
    if user_id not in users_data:
        await message.answer("Ваш профиль не найден. Сначала настройте профиль с помощью /set_profile.")
        return

    # Список обязательных ключей и их сообщений об ошибке
    required_keys = {
        'logged_water': "Количество выпитой воды не найдено.\nСначала запишите её с помощью /log_water.",
        'logged_calories': "Количество потребленных калорий не найдено.\nСначала запишите их с помощью /log_food.",
        'burned_calories': "Количество сожжённых калорий не найдено.\nСначала запишите их с помощью /log_workout."}

    # Проверяем наличие каждого ключа
    for key, error_message in required_keys.items():
        if key not in users_data[user_id]:
            await message.answer(error_message)
            return

    # Достаём данные по воде и калориям
    logged_water = users_data[user_id]['logged_water']
    water_goal = users_data[user_id]['water_goal']
    if round(water_goal - logged_water) <= 0:
        water_left = 0
    else:
        water_left = round(water_goal - logged_water)

    logged_calories = users_data[user_id]['logged_calories']
    calorie_goal = users_data[user_id]['calorie_goal']
    burned_calories = users_data[user_id]['burned_calories']
    balance_calories = round(logged_calories - burned_calories)

    # Формирование текста ответа
    result_text = ("Ваш прогресс:\nВода:\n"
                   f"- Выпито: {logged_water} мл из {water_goal} мл.\n"
                   f"- Осталось: {water_left} мл.\n\nКалории:\n"
                   f"- Потреблено: {logged_calories} ккал. из {calorie_goal} ккал.\n"
                   f"- Сожжено: {burned_calories} ккал.\n"
                   f"- Баланс: {balance_calories}\n")

    # Проверки по воде и калориям
    if balance_calories <= calorie_goal:
        result_text += "Вы находитесь в балансе по калориям, так держать!"
    elif balance_calories > calorie_goal:
        result_text += (
            f"Для баланса по калориям необходимо сжечь не менее {balance_calories - calorie_goal} ккал.\n"
            "Наиболее подходящими тренировками для этого будут Плавание и Кардио.")
    elif water_left <= 0:
        result_text += ("Вы выпили дневную норму воды, так держать!")
    elif water_left > 0:
        result_text += (f"До выполнения нормы осталось выпить {water_left} мл.")
    elif balance_calories > calorie_goal and water_left > 0:
        result_text += (
            f"Для баланса по калориям необходимо сжечь не менее {balance_calories - calorie_goal} ккал.\n"
            "Наиболее подходящими тренировками для этого будут Плавание и Кардио.\n"
            f"До выполнения нормы осталось выпить {water_left} мл.\n"
            "Продолжайте в том же духе, у вас всё получится!")

    # Отправка сообщения и завершение состояния
    await message.answer(result_text)
    await state.clear()


# Подключение обработчиков
def setup_handlers(dp):
    dp.include_router(router)
