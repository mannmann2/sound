import requests
from datetime import datetime
from threading import Thread
from config import es, ConflictError


def make_request(url, username, token=None):

    if not token:
        user = es.get('users', '_doc', username)['_source']
        token = user['access_token']
    headers = {"Authorization": "Bearer " + token}
    js = requests.get(url, headers=headers).json()
    if 'error' in js:
        if js['error']['message'] == "The access token expired":
            return make_request(url, username, refresh(username, user['refresh_token']))
        # elif js['error']['message'] == "Permissions missing":
        #     return None
    else:
        return js


def refresh(username, refresh_token):

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": 'e6f5f053a682454ca4eb1781064d3881',
        "client_secret": "e4294f2365ec45c0be87671b0da16596"
        }

    js = requests.post("https://accounts.spotify.com/api/token", data=data).json()
    # print(js)

    token = js['access_token']
    es.update('users', '_doc', username, {'doc': {'access_token': token}})


def get_recent(username):
    url = "https://api.spotify.com/v1/me/player/recently-played?limit=50"
    js = make_request(url, username)

    ids = ''
    for item in js['items']:
        track = item.get('track')
        # track = item.pop('track')
        es.index('simple-track', '_doc', track, track['id'])
        ids += track['id'] + ','

        try:
            dt = datetime.strptime(item['played_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            dt = datetime.strptime(item['played_at'], '%Y-%m-%dT%H:%M:%SZ')
        ms = str(int(dt.timestamp() * 1000))

        item['played_by'] = username
        # item['track_id'] = track['id']
        try:
            es.index('recent', '_doc', item, username+':'+ms+':'+track['id'], op_type='create', ignore=[409])
        except ConflictError:
            pass
        item['track'] = track

    if ids:
        Thread(target=get_features, args=(username, ids[:-1])).start()
    return js


def get_friends(username):
    return es.get('friends', '_doc', username)['_source']['friends']


def add_friend(friend1, friend2):
    friends = get_friends(friend1)
    if friend2 not in friends:
        friends.append(friend2)
        es.index('friends', '_doc', {'friends': friends}, friend1)

        friends = get_friends(friend2)
        friends.append(friend1)
        es.index('friends', '_doc', {'friends': friends}, friend2)


def get_messages(username, friend):
    query = {
        "query": {
            "query_string": {
                "query": '((from:'+username+' AND to:'+friend+') OR (from:'+friend+' AND to:'+username+'))'
            }
        },
        'sort': {'timestamp': {'order': 'desc'}}
    }
    return es.search('messages', '_doc', query)['hits']['hits']


def send_message(from_, to_, message_):
    es.index('messages', '_doc', {'from': from_, 'to': to_, 'message': message_, 'timestamp': datetime.now()})


def get_features(username, ids):
    url = "https://api.spotify.com/v1/audio-features?ids=" + ids
    js = make_request(url, username)['audio_features']

    for item in js:
        try:
            es.index('features', '_doc', item, item['id'])
        except TypeError:
            pass
    return js


def get_analysis(username, id_):
    url = "https://api.spotify.com/v1/audio-analysis/" + id_
    js = make_request(url, username)

    es.index('analysis', '_doc', js, id_)
    return js


def get_artist(artist_id):
    return es.get('artist', '_doc', artist_id)['_source']


def get_following(username):
    return es.get('following', '_doc', username)['_source']['ids']


def get_all_following(username):
    url = "https://api.spotify.com/v1/me/following?type=artist&limit=50" #&after=" + params['after']
    js = make_request(url, username)

    ids = []
    while True:
        for item in js['artists']['items']:
            es.index('artist', '_doc', item, item['id'])
            ids.append(item['id'])

        if js['artists']['next']:
            js = make_request(js['artists']['next'], username)
        else:
            break

    es.index('following', '_doc', {'ids': ids}, username)

    # if '/' in item['name']:
    #     item['name'] = item['name'].replace('/', ' ')
    # if item['images']:
    #     img = item['images'][-1]['url']
    # else:
    #     img = ''
    # foll.append((item['name'], item['id'], img, item['popularity']))


# def index(index_name, body, id_):
    # try:
    #     es.index(index_name, '_doc', body, id_, op_type='create')
    # except ConflictError:
    #     pass
