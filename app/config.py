import os
from redis import Redis
from urllib.parse import urlparse

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
url = urlparse(redis_url)

redis_client = Redis(
    host=url.hostname,
    port=url.port,
    password=url.password,
    decode_responses=True,
    ssl=url.scheme == 'rediss'  # SSL 사용 여부 확인
)

# Redis 연결 테스트 함수
def test_redis_connection():
    try:
        redis_client.ping()
        print("Successfully connected to Redis")
        return True
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        return False