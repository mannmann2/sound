import time
import schedule
from helpers import refresh, get_recent
from config import es

query = {
    'query': {
        'match_all': {}
    }, 'size': 10000
}


def recents():
    users = es.search('users', doc_type='_doc', body=query)['hits']['hits']
    for user in users:
        print(user['_id'])
        get_recent(user['_id'])

# schedule.every(10).minutes.do(recents)
schedule.every().hour.do(recents)

while True:
    schedule.run_pending()
    time.sleep(60)
