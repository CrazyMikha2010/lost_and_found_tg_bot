"""
run this code if you'll have error about webhook
"""

import requests

TOKEN = "" # paste yout API token here
url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
response = requests.get(url)
print(response.json())
