import asyncio
import logging
import os

from redis.asyncio import Redis


logging.basicConfig(level=os.getenv("MBAS_LOG_LEVEL", "INFO"))
log = logging.getLogger("mbas.worker")


async def main() -> None:
    redis = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
    log.info("MBAs worker started")
    try:
        while True:
            job = await redis.blpop("mbas:jobs", timeout=5)
            if job:
                _, payload = job
                # Future jobs: knowledge ingestion, follow-ups, provider retries, evaluation runs.
                log.info("Received job: %s", payload)
    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())

