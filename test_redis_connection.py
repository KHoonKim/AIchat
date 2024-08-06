import os
from redis import Redis
from urllib.parse import urlparse

# 환경 변수에서 Redis URL을 가져옴
redis_url = os.getenv('UPSTASH_REDIS_URL')

if redis_url:
    url = urlparse(redis_url)
    redis_client = Redis(
        host=url.hostname,
        port=url.port,
        password=url.password,
        ssl=url.scheme == 'rediss',
        ssl_cert_reqs=None,
        decode_responses=True
    )
else:
    redis_client = None

def test_redis_connection():
    if redis_client is None:
        print("No Redis URL provided")
        return False
    try:
        redis_client.ping()
        print("Successfully connected to Redis")
        return True
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        return False

# 테스트 실행
if __name__ == "__main__":
    test_redis_connection()