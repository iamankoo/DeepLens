import sys

from rq import Worker
from rq.worker import SimpleWorker

from app.core.logger import logger
from app.queue.connection import redis_conn, research_queue


def main():
    # RQ's default Worker forks a child process per job (os.fork), which
    # doesn't exist on Windows and silently never dequeues anything there —
    # SimpleWorker runs jobs in-process instead and is the supported choice
    # on this platform.
    worker_cls = SimpleWorker if sys.platform == "win32" else Worker

    logger.info(
        "starting RQ worker",
        extra={"worker_class": worker_cls.__name__, "queue": research_queue.name},
    )

    worker = worker_cls([research_queue], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
