import requests


# Поиск калорийности продукта
def get_food_info(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        if products:  # Проверяем, есть ли найденные продукты
            first_product = products[0]
            return {
                'name': first_product.get('product_name', 'Неизвестно'),
                'calories': first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
            }
        return None
    print(f"Ошибка: {response.status_code}")
    return None


# Расчёт нормы воды
def calculate_water(weight, activity):
    base_water = weight * 35  # средний коэффициент
    activ_water = activity * 500 / 60  # 500 мл на час активности
    return round(base_water + activ_water, 1)


# Расчёт нормы калорий
def calculate_calories(weight, height, age, activity):
    clrs = 10 * weight + 6.25 * height - 5 * age + 5
    return round(clrs * activity / 60, 1)


# Получение температуры в заданном городе
def get_temp(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        curr_temp = weather_data['main']['temp']
        return curr_temp
    else:
        return 20  # заглушка, если api упадёт
