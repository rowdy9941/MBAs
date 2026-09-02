import asyncio
from datetime import UTC, datetime
import json
import logging
import os

from redis.asyncio import Redis


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "payload_size"):
            event["payload_size"] = record.payload_size
        return json.dumps(event, separators=(",", ":"))


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=os.getenv("MBAS_LOG_LEVEL", "INFO"), handlers=[handler])
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
                log.info("Job received", extra={"payload_size": len(payload)})
    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
