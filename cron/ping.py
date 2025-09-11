from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
import os
from dotenv import load_dotenv

load_dotenv()

PING_URL = os.getenv("PING_URL")

def run_ping():

    print("Starting Ping cron job")
    try:
        if not PING_URL:
            print("PING_URL is not set in environment variables.")
            return
        response = requests.get(PING_URL)
        if response.status_code == 200:
            print("Ping successful")
        else:
            print(f"Ping failed with status code: {response.status_code}")
    except Exception as e:
        print(
            f"Error in refreshing KB Links Content cron job: {str(e)}")


scheduler = BackgroundScheduler()
# Run every 60 seconds
trigger = CronTrigger(second=59)
scheduler.add_job(run_ping, trigger)
