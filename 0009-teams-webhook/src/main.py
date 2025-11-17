import json
import os

import requests
from dotenv import load_dotenv

_ = load_dotenv()

WEBHOOK = os.getenv("WEBHOOK")

if not WEBHOOK:
    raise ValueError("WEBHOOK environment variable is not set")

def send_teams_message(message: str, webhook_url: str = WEBHOOK) -> requests.Response:
    headers = {"Content-Type": "application/json"}
    data = {"message": message}
    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
    return response
