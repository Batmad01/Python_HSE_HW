# Образ Python
FROM python:3.10-slim

# Рабочая директория
WORKDIR /app

# Зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файлы 
COPY . .

# Копируем скрипт app.sh внутрь контейнера
COPY docker/app.sh /docker/app.sh
RUN chmod a+x docker/*.sh