"""Background scheduler — runs consolidation, dimension updates, reflections, and emotion ticks.

Uses APScheduler for reliable scheduling instead of sleep+tick accumulation.
Now each task creates its own DB session only when it actually executes.
"""
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.core.database import SessionLocal


class TaskScheduler:
    def __init__(self):
        self._running = False
        self._scheduler = BackgroundScheduler(daemon=True)

    def _run_hourly_tasks(self):
        """Run tasks every ~60 seconds."""
        db = SessionLocal()
        try:
            from app.services.consolidation import ConsolidationService
            ConsolidationService(db).consolidate_hourly()
            from app.services.user_model import UserModelService
            UserModelService(db).update_dimensions()
            UserModelService(db).update_state()
            from app.services.behavior_mapping import BehaviorMappingService
            BehaviorMappingService(db).scan_hourly()
            from app.services.reflection import ReflectionService
            ReflectionService(db).generate_hourly_reflection()
        except Exception as e:
            logger.warning(f"Hourly task error: {e}")
        finally:
            db.close()

    def _run_entity_enrich(self):
        """Run entity enrichment every ~30 seconds."""
        try:
            from app.services.llm_entity_extractor import batch_enrich_entities
            batch_enrich_entities()
        except Exception as e:
            logger.warning(f"Entity enrich error: {e}")

    def _run_daily_tasks(self):
        """Run daily tasks once per day."""
        db = SessionLocal()
        try:
            from app.services.consolidation import ConsolidationService
            ConsolidationService(db).consolidate_daily()
            from app.services.reflection import ReflectionService
            ReflectionService(db).generate_daily_reflection()
        except Exception as e:
            logger.warning(f"Daily task error: {e}")
        finally:
            db.close()

    def _run_weekly_tasks(self):
        """Run weekly tasks once per week."""
        db = SessionLocal()
        try:
            from app.services.consolidation import ConsolidationService
            ConsolidationService(db).consolidate_weekly()
        except Exception as e:
            logger.warning(f"Weekly task error: {e}")
        finally:
            db.close()

    def _run_emotion_tasks(self):
        """Run emotion collection and computation every ~5 minutes."""
        db = SessionLocal()
        try:
            from app.services.emotion_collector import collect_all
            from app.algorithms.emotion_engine import compute_current
            collect_all(db)
            compute_current(db)
        except Exception as e:
            logger.warning(f"Emotion tick error: {e}")
        finally:
            db.close()

    def start(self):
        if self._running:
            return
        self._running = True

        # Hourly: consolidation + user model + behavior + reflection
        self._scheduler.add_job(
            self._run_hourly_tasks,
            IntervalTrigger(seconds=60),
            id="hourly_tasks",
            replace_existing=True,
        )

        # Entity enrichment every 30 seconds
        self._scheduler.add_job(
            self._run_entity_enrich,
            IntervalTrigger(seconds=30),
            id="entity_enrich",
            replace_existing=True,
        )

        # Emotion every 5 minutes
        self._scheduler.add_job(
            self._run_emotion_tasks,
            IntervalTrigger(minutes=5),
            id="emotion_tasks",
            replace_existing=True,
        )

        # Daily at 2:00 AM
        self._scheduler.add_job(
            self._run_daily_tasks,
            CronTrigger(hour=2, minute=0),
            id="daily_tasks",
            replace_existing=True,
        )

        # Weekly on Monday at 3:00 AM
        self._scheduler.add_job(
            self._run_weekly_tasks,
            CronTrigger(day_of_week=0, hour=3, minute=0),
            id="weekly_tasks",
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info("Task scheduler started with APScheduler")

    def stop(self):
        self._running = False
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Task scheduler stopped")


scheduler = TaskScheduler()
