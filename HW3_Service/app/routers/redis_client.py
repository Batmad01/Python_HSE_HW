import redis
from app.config import REDIS_HOST, REDIS_PORT

# Подключение клиента Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
