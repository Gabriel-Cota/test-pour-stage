import os
import json
import requests
from datetime import datetime, timedelta, date
from collections import Counter
import pytz

NOTION_TOKEN = os.environ['NOTION_TOKEN']
DATABASE_ID = 'eb7d566caa5683ddbde88137ddf476c1'
DAILY_GOAL = 10

headers = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

def query_database():
    pages = []
    cursor = None
    while True:
        body = {'page_size': 100}
        if cursor:
            body['start_cursor'] = cursor
        r = requests.post(
            f'https://api.notion.com/v1/databases/{DATABASE_ID}/query',
            headers=headers,
            json=body
        )
        data = r.json()
        pages.extend(data.get('results', []))
        if not data.get('has_more'):
            break
        cursor = data.get('next_cursor')
    return pages

pages = query_database()

tz = pytz.timezone('Europe/Paris')
today = datetime.now(tz).date()

app_dates = []
statuses = Counter()

for page in pages:
    props = page.get('properties', {})

    date_prop = props.get('Date de la candidature', {})
    if date_prop.get('type') == 'date' and date_prop.get('date'):
        try:
            app_dates.append(date.fromisoformat(date_prop['date']['start']))
        except:
            pass

    status_prop = props.get('Statut de la candidature', {})
    if status_prop.get('type') == 'status' and status_prop.get('status'):
        statuses[status_prop['status']['name']] += 1

date_counter = Counter(app_dates)
today_count = date_counter.get(today, 0)

# Last 7 days
last7, labels = [], []
for i in range(6, -1, -1):
    d = today - timedelta(days=i)
    last7.append(date_counter.get(d, 0))
    labels.append(d.strftime('%a'))

# Streak: consecutive days ending today (or yesterday) with >= DAILY_GOAL apps
streak = 0
check = today if today_count >= DAILY_GOAL else today - timedelta(days=1)
while date_counter.get(check, 0) >= DAILY_GOAL:
    streak += 1
    check -= timedelta(days=1)

output = {
    'total': len(app_dates),
    'today': today_count,
    'goal': DAILY_GOAL,
    'streak': streak,
    'labels': labels,
    'last7': last7,
    'statuses': {
        'Appliqué': statuses.get('Appliqué', 0),
        'Entretien': statuses.get('Entretien', 0),
        'Refusé': statuses.get('Refusé', 0),
    },
    'updated_at': datetime.now(tz).strftime('%d/%m/%Y %H:%M')
}

with open('data.json', 'w') as f:
    json.dump(output, f)

print(json.dumps(output, indent=2))
