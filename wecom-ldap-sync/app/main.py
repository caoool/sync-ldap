"""Entry point: runs sync on a schedule."""
import logging
import sys

from apscheduler.schedulers.blocking import BlockingScheduler

from app.config import settings
from app.sync import run_sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main():
    if not settings.wecom_corpid or not settings.wecom_corpsecret:
        logger.error(
            "WECOM_CORPID and WECOM_CORPSECRET must be set. "
            "Create a self-built app with contacts read permission in WeCom Admin."
        )
        sys.exit(1)

    # Run once immediately at startup
    logger.info("Running initial sync…")
    try:
        run_sync()
    except Exception:
        logger.exception("Initial sync failed, will retry on schedule")

    # Schedule periodic sync
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_sync,
        "interval",
        minutes=settings.sync_interval_minutes,
        id="wecom_ldap_sync",
        max_instances=1,
        coalesce=True,
    )
    logger.info(
        "Scheduler started — syncing every %d minutes", settings.sync_interval_minutes
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler")


if __name__ == "__main__":
    main()
