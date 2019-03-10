import requests
from datetime import datetime
from config import es

def make_request(url, username):

    user = es.get('users', doc_type='_doc', id=username)['_source']
    headers = {"Authorization": "Bearer " + user['access_token']}
    js = requests.get(url, headers=headers).json()
    if 'error' in js:
        if js['error']['message'] == "The access token expired":
            refresh(user)
            return make_request(url, username)
        # elif js['error']['message'] == "Permissions missing":
        #     return None
    else:
        return js

def refresh(user):

    data = {
        "grant_type": "refresh_token",
        "refresh_token": user['refresh_token'],
        "client_id": 'e6f5f053a682454ca4eb1781064d3881',
        "client_secret": "e4294f2365ec45c0be87671b0da16596"
        }

    js = requests.post("https://accounts.spotify.com/api/token", data=data).json()
    # print(js)

    user['access_token'] = js['access_token']
    es.index('users', doc_type='_doc', id=user['id'], body=user)
    # return token

def get_recent(username):
    url = "https://api.spotify.com/v1/me/player/recently-played?limit=50"
    js = make_request(url, username)

    ids = ''
    for item in js['items']:
        try:
            dt = datetime.strptime(item['played_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            dt = datetime.strptime(item['played_at'], '%Y-%m-%dT%H:%M:%SZ')

        ms = str(int(dt.timestamp() * 1000))

        es.index('simple-track', doc_type='_doc', id=item['track']['id'], body=item['track'])
        ids += item['track']['id'] + ','

        item['played_by'] = username
        es.index('recent', doc_type='_doc', id=username+':'+ms+':'+item['track']['id'], body=item)

    if ids:
        get_features(username, ids[:-1])
    return js


def get_features(username, ids):
    url = "https://api.spotify.com/v1/audio-features?ids=" + ids
    js = make_request(url, username)['audio_features']

    for item in js:
        try:
            es.index('features', '_doc', id=item['id'], body=item)
        except TypeError:
            pass
    return js

def get_analysis(username, id_):
    url = "https://api.spotify.com/v1/audio-analysis/" + id_
    js = make_request(url, username)

    es.index('analysis', '_doc', id=id_, body=js)
    return js


def get_friends(username):
    friends = es.get('friends', doc_type='_doc', id=username)['_source']['friends']
    return friends

def add_friend(friend1, friend2):
    friends = get_friends(friend1)
    if friend2 not in friends:
        friends.append(friend2)
        es.index('friends', doc_type='_doc', id=friend1, body={'friends':friends})

        friends = get_friends(friend2)
        friends.append(friend1)
        es.index('friends', doc_type='_doc', id=friend2, body={'friends':friends})

def get_artist(artist_id):
    return es.get('artist', doc_type='_doc', id=artist_id)['_source']

def get_following(username):
    return es.get('following', doc_type='_doc', id=username)['_source']['ids']

def get_all_following(username):
    url = "https://api.spotify.com/v1/me/following?type=artist&limit=50" #&after=" + params['after']
    js = make_request(url, username)

    ids = []
    while True:
        for item in js['artists']['items']:
            es.index('artist', doc_type='_doc', id=item['id'], body=item)
            ids.append(item['id'])

        if js['artists']['next']:
            js = make_request(js['artists']['next'], username)
        else:
            break

    es.index('following', doc_type='_doc', id=username, body={'ids':ids})

    # if '/' in item['name']:
    #     item['name'] = item['name'].replace('/', ' ')
    # if item['images']:
    #     img = item['images'][-1]['url']
    # else:
    #     img = ''
    # foll.append((item['name'], item['id'], img, item['popularity']))

def message(from_, to_, message_):
    es.index('messages', '_doc', body={'from': from_, 'to': to_, 'message': message_, 'timestamp': datetime.now()})

def get_messages(username, friend):
    query = {
        "query": {
            "query_string": {
                "query": '((from:'+username+' AND to:'+friend+') OR (from:'+friend+' AND to:'+username+'))'
            }
        },
        'sort': {'timestamp': {'order': 'asc'}}
    }
    return es.search('messages', '_doc', body=query)['hits']['hits']
