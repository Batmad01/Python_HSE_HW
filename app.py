import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go


# Функция для расчета скользящего среднего за 30 дней
def moving_avg(group):
    group['moving_average'] = group.groupby('city')['temperature'].transform(
        lambda x: x.rolling(window=30, min_periods=1).mean())
    return group


# Функция для вычисления сезонных статистик и выделения аномалий
def season_stats(group):
    stats = group.groupby(['season', 'city'])['temperature'].agg(['mean', 'std']).reset_index()
    group = group.merge(stats, on=['season', 'city'], suffixes=('', '_seasonal'))
    group['anomaly'] = abs(group['temperature'] - group['mean']) > 2 * group['std']
    return group


# Заголовок
st.title("Анализ погодных данных")

# Загрузка данных
st.header("Загрузка данных")
df = st.file_uploader("Выберите CSV-файл", type=["csv"])

if df is not None:
    # Превью данных и выбор города
    data = pd.read_csv(df)
    st.write("Превью данных:")
    st.dataframe(data, use_container_width=True)

    st.title("Выбор города")
    cities = data['city'].unique()
    city = st.selectbox("Выберите город:", cities)

    # Описательные статистики для выбранного города
    data_groups = [group for _, group in data.groupby('city')]
    data = pd.concat([moving_avg(group) for group in data_groups], ignore_index=True)
    data = pd.concat([season_stats(group) for group in data_groups], ignore_index=True)

    filtered_city = data[data['city'] == city]
    st.write(f"Вы выбрали: {city}")
    st.dataframe(filtered_city, use_container_width=True)

    # Графики
    # Подготовка данных для первого графика
    season_order = ['autumn', 'winter', 'spring', 'summer']
    data['season'] = pd.Categorical(data['season'], categories=season_order, ordered=True)
    seasonal_stats = (data.groupby(['season', 'city'], observed=False)
                      ['temperature'].agg(['mean', 'std']).reset_index())

    # Средняя температура по сезонам
    fig1 = go.Figure()
    for city_ in seasonal_stats['city'].unique():
        city_data = seasonal_stats[seasonal_stats['city'] == city_]
        fig1.add_trace(go.Scatter(x=city_data['season'], y=city_data['mean'],
                                  mode='lines+markers', name=city_))
        fig1.update_layout(title='Средняя температура по сезонам в разных городах',
                           xaxis_title='Сезон', yaxis_title='Средняя температура (°C)',
                           legend_title='Город', template='plotly_white')

    # Подготовка данных для второго графика
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    city_data = data[data['city'] == city]
    city_anomalies = city_data[city_data['anomaly']]

    # Температуры и аномалии
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=city_data['timestamp'], y=city_data['moving_average'],
                              mode='lines', name='Температура'))
    fig2.add_trace(go.Scatter(x=city_anomalies['timestamp'], y=city_anomalies['moving_average'],
                              mode='markers', marker=dict(color='green', size=6), name='Аномалия'))

    fig2.update_layout(title=f'Температура и аномалии в {city}', xaxis_title='Год',
                       yaxis_title='Температура (°C)', legend_title='Легенда',
                       template='plotly_white')

    st.title("Визуализации")
    st.plotly_chart(fig1)
    st.plotly_chart(fig2)

    # Сохранение API-ключа
    st.title("Текущая погода в городе")
    if "api_key" not in st.session_state:
        st.session_state["api_key"] = ""

    # Форма для ввода API-ключа
    with st.form("api_key_form"):
        api_key = st.text_input("Введите API-ключ OpenWeatherMap:",
                                value=st.session_state["api_key"])
        submit = st.form_submit_button("Сохранить")
        if submit:
            st.session_state["api_key"] = api_key
            st.success("API-ключ сохранен!")

    # Если введён API-ключ
    if st.session_state["api_key"]:
        # Запрос текущей погоды в выбранном городе
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)
        if response.status_code == 200:
            weather_data = response.json()
            curr_temp = weather_data['main']['temp']
            st.success(f"Погода в {city}:")
            st.write(f"Температура: {weather_data['main']['temp']} °C")
            st.write(f"Описание: {weather_data['weather'][0]['description']}")

            # Получение средней температуры для сезона и города
            city_stats = seasonal_stats[seasonal_stats['city'] == city]
            season_stats = city_stats[city_stats['season'] == 'winter']
            mean_temp = season_stats['mean'].values[0]

            # Сравнение текущей температуры с нормальной (средней)
            if curr_temp < mean_temp - 5:
                st.warning(f"Температура ниже нормы для сезона. Ожидаемая: {mean_temp:.2f}°C")
            elif curr_temp > mean_temp + 5:
                st.warning(f"Температура выше нормы для сезона. Ожидаемая: {mean_temp:.2f}°C")
            else:
                st.success(f"Температура в пределах нормы для сезона. Ожидаемая: {mean_temp:.2f}°C")

        elif response.status_code == 401:
            st.error(f"{response.json()}")
        else:
            st.error(f"Код ошибки {response.status_code}")
    else:
        st.warning("Пожалуйста, введите API-ключ.")
else:
    st.write("Пожалуйста, загрузите CSV-файл.")
