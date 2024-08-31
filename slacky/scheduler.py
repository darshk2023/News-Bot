import logging
from slack_sdk import WebClient
from django.conf import settings
from events.Sharingan_Summarizer import Sharingan_Summarizer
from slack_sdk.errors import SlackApiError
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events

logger = logging.getLogger(__name__)
SLACK_BOT_USER_TOKEN = getattr(settings, 'SLACK_BOT_USER_TOKEN', None)
Client = WebClient(SLACK_BOT_USER_TOKEN)

def send_daily_summary():
    '''
    Using my Sharingan_Summarizer Class, a summary of the top 3 news source's top 3 articles is 
    created and sent to the tomoe slack bot message to me.
    '''
    sources = [
        "https://www.cnn.com/",
        "https://www.foxnews.com/",
        "https://www.nbcnews.com/"
    ]
    css_selectors = [
        ".container__headline-text",  # Updated selector: targets the headline titles
        ".title",
        ".multistoryline__headline"
    ]
    
    try:
        # Create Bot Message
        tomoe_summarizer = Sharingan_Summarizer(sources, css_selectors)
        # Define the file path
        file_path = tomoe_summarizer.get_save_path()

        # Open and read the file
        with open(file_path, 'r') as file:
            content = file.read()

        bot_text = f'Hello, good morning!!\nHere is today\'s news:\n{content}'
        channel = 'C076EBB7CUW'

        Client.chat_postMessage(channel=channel, text=bot_text)
        logger.info(f'Sent daily summary to channel {channel}')
    except SlackApiError as e:
        logger.error(f"Error posting message: {e.response['error']}")
def start():
    # Intialize background scheduler and add job store to it (APScheduler will keep the job data here)
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    # Add new job to the scheduler
    scheduler.add_job(
        send_daily_summary,
        trigger=CronTrigger(hour="11", minute="15"),
        id="daily_summary",
        replace_existing = True
    )
    # Registers scheduler's events with Django and start execution of scheduled jobs
    register_events(scheduler)
    scheduler.start()
    logger.info("Scheduler Started")



