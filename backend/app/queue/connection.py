import redis
from rq import Queue

from app.core.config import settings

redis_conn = redis.from_url(settings.REDIS_URL)

research_queue = Queue(settings.RESEARCH_QUEUE_NAME, connection=redis_conn)
