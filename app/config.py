import os
from redis import Redis
from urllib.parse import urlparse

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
url = urlparse(redis_url)
redis_client = Redis(host=url.hostname, port=url.port, password=url.password, decode_responses=True)