import logging
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
from .cron import FetchYouTubeVideosCronJob

logger = logging.getLogger(__name__)

# Configure the scheduler to use threads explicitly
executors = {
    'default': ThreadPoolExecutor(20)  # Adjust the number of threads as needed
}

scheduler = BackgroundScheduler(executors=executors)
scheduler.add_jobstore(DjangoJobStore(), "default")

# Register the job function from cron.py
@register_job(scheduler, IntervalTrigger(hours=24), id="fetch_youtube_videos", replace_existing=True)
def scheduled_job():
    try:
        # Create an instance of the FetchYouTubeVideosCronJob and call its do method
        job = FetchYouTubeVideosCronJob()
        job.do()
        logger.info("Successfully fetched YouTube videos.")
    except Exception as e:
        logger.error(f"Error during YouTube video fetching: {e}")

register_events(scheduler)

def start_scheduler():
    """
    Function to manually start the scheduler.
    """
    if not scheduler.running:
        try:
            scheduler.start()
            logger.info("Scheduler started.")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")

def stop_scheduler():
    """
    Function to manually stop the scheduler.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
