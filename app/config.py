import os
from redis import Redis
from urllib.parse import urlparse
import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

redis_url = os.getenv('UPSTASH_REDIS_URL')  # UPSTASH_REDIS_URL을 사용

if redis_url:
    url = urlparse(redis_url)
    logger.debug(f"Parsed Redis URL: {url}")
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
    logger.warning("No Redis URL provided")

def test_redis_connection():
    if redis_client is None:
        print("No Redis URL provided")
        return False
    try:
        redis_client.ping()
        print("Successfully connected to Redis")
        logger.info("Successfully connected to Redis")
        return True
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        logger.error(f"Failed to connect to Redis: {e}")
        return False