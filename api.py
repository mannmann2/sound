import flask
from flask import request

import json
import requests
from threading import Thread

from helpers import get_following, get_all_following, get_artist, get_recent, make_request, add_friend, get_friends, message, get_messages, get_features, get_analysis
from config import es

app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/api/v1/feed', methods=['GET'])
def feed():
    params = request.args
    Q = ' OR '.join([params['username']] + get_friends(params['username']))
    Q1 = {
        "query": {
            "query_string": {
                "query": "played_by: " + Q
            }
        },
        "sort": {"played_at": {"order": "desc"}},
        "size": 200,
    }
    items = []
    for item in es.search('recent', body=Q1)['hits']['hits']:
        # track_id = item['_source'].pop('track_id')
        # track_id = item['_id'].split(':')[2]
        # item['_source']['track'] = es.get('simple-track', '_doc', track_id)['_source']
        items.append(item['_source'])
    return str({'items': items})

@app.route('/api/v1/trending', methods=['GET'])
def trending():
    params = request.args

    Q = ' OR '.join(get_friends(params['username']))
    Q1 = {
        "query": {
            "bool": {
                "must": {
                    "range": {
                        "played_at": {"gte": "now-24h/h", "lte": "now/h"}
                    }
                },
                "filter": {"match": {"played_by": Q}}
            }
        },
        "size": 0,
        "aggs": {
            "artists": {"terms": {"field": "track.artists.name.keyword",
                                  "size": 42}},
        }
    }
    Q2 = {
        "query": {
            "bool": {
                "must": {
                    "range": {
                        "played_at": {"gte": "now-7d/d", "lte": "now/d"}
                    }
                },
                "filter": {"match": {"played_by": Q}}
            }
        },
        "size": 0,
        "aggs": {
            "artists": {"terms": {"field": "track.artists.name.keyword",
                                  "size": 42}},
        }
    }

    agg = es.search('recent', body=Q1)['aggregations']['artists']['buckets']
    agg2 = es.search('recent', body=Q2)['aggregations']['artists']['buckets']
    return str([agg, agg2])

@app.route('/api/v1/top-genres', methods=['GET'])
def top_genres():
    params = request.args

    genres = {}
    for artist_id in get_following(params['username']):
        artist = get_artist(artist_id)
        for genre in artist['genres']:
            if genre in genres:
                genres[genre] += 1
            else:
                genres[genre] = 1

    genres = sorted([[key, val] for (key, val) in genres.items()], key=lambda x: x[1], reverse=True)
    return str(genres)

@app.route('/api/v1/genre-artists', methods=['GET'])
def genres():
    params = request.args

    artists = []
    for artist_id in get_following(params['username']):
        artist = get_artist(artist_id)
        if params['genre'].replace('+', ' ') in artist['genres']:
            artists.append(artist)

    return str(artists)


# @app.route('/api/v1/played', methods=['POST'])
# def played():
#     params = request.form

#     es.index('played', '_doc', params, id=params['id'])
#     return str()

# @app.route('/api/v1/shared', methods=['POST'])
# def shared():
#     params = request.form

#     es.index('shared', '_doc', params, id=params['id'])

@app.route('/api/v1/get-friends', methods=['GET'])
def getfriends():
    params = request.args
    friends = get_friends(params['username'])
    friends = [es.get('users', '_doc', id=friend)['_source'] for friend in friends]

    return str(friends)

@app.route('/api/v1/add-friend', methods=['GET'])
def addfriend():
    params = request.args
    add_friend(params['username'], params['friend'])
    return


@app.route('/api/v1/get-messages', methods=['GET'])
def getmessage():
    params = request.args
    messages = get_messages(params['username'], params['friend'])
    return str(messages)

@app.route('/api/v1/send-message', methods=['GET'])
def sendmessage():
    params = request.args
    message(params['username'], params['friend'], params['message'])
    return ''


# @app.route('/api/v1/login1', methods=['GET'])
# def login1():
#     params = request.args
#     code = params['code']
#     uri = 'https://www.google.com'

#     data = {
#         "grant_type": "authorization_code",
#         "code": code,
#         "redirect_uri": uri,
#         "client_id": 'e6f5f053a682454ca4eb1781064d3881',
#         "client_secret": "e4294f2365ec45c0be87671b0da16596"
#     }
#     js = requests.post("https://accounts.spotify.com/api/token", data=data).json()
#     return str(js)


@app.route('/api/v1/login', methods=['GET'])
def login():
    params = request.args
    token = params['access_token']

    url = "https://api.spotify.com/v1/me"
    headers = {"Authorization": "Bearer " + token}
    js = requests.get(url, headers=headers).json()

    js['access_token'] = token
    js['refresh_token'] = params['refresh_token']
    es.index('users', '_doc', id=js['id'], body=js)

    Thread(target=get_all_following, args=(js['id'],)).start()
    Thread(target=get_recent, args=(js['id'],)).start()
    return str(js)


@app.route('/api/v1/user', methods=['GET'])
def users():
    # change this to get user from es directly
    params = request.args

    url = "https://api.spotify.com/v1/me"
    js = make_request(url, params['username'])

    es.index('users', '_doc', id=js['id'], body=js)

    return str(js)


@app.route('/api/v1/analysis', methods=['GET'])
def analysis():
    params = request.args
    js = get_analysis(params['username'], params['id'])

    return str(js)


@app.route('/api/v1/features', methods=['GET'])
def features():
    params = request.args
    js = get_features(params['username'], params['ids'])

    return str(js)


@app.route('/api/v1/search', methods=['GET'])
def search():
    params = request.args

    url = "https://api.spotify.com/v1/search?q=*" + params['query'] + "*&type=album,artist,track&limit=50"
    js = make_request(url, params['username'])

    # albs = []
    for item in js['albums']['items']:
        es.index('simple-album', '_doc', id=item['id'], body=item)
        # if item['images']:
        #     img3 = item['images'][-1]['url']
        # else:
        #     img3 = ''
        # albs.append((item['name'], item['id'], item['release_date'][:4], item['album_type'], img3))

    # arts = []
    for item in js['artists']['items']:
        es.index('artist', '_doc', id=item['id'], body=item)
        # # if '/' in item['name']:
        # #     item['name'] = item['name'].replace('/', ' ')
        # if item['images']:
        #     img = item['images'][-1]['url']
        # else:
        #     img = ''
        # arts.append((item['name'], item['id'], img, item['popularity']))

    # trks = []
    for item in js['tracks']['items']:
        es.index('track', '_doc', id=item['id'], body=item)
        # dur = get_time(item['duration_ms'])
        # trks.append((item['name'], dur, item['external_urls']['spotify']))

    return str(js)

        # dur = get_time(item['track']['duration_ms'])
        # recents.append((item['track']['name'], item['track']['external_urls']['spotify'],
        #                 item['track']['album']['artists'][0]['name'], item['track']['album']['artists'][0]['id'], item['track']['album']['name'], item['track']['album']['id'], dur, parse(item['played_at']), item['track']['album']['images'][2]['url']))
                        # (dt.timestamp()+19800).strftime('%B %d, %-I:%M %p')))


@app.route('/api/v1/recently-played', methods=['GET'])
def recent():
    params = request.args
    return str(get_recent(params['username']))


@app.route('/api/v1/currently-playing', methods=['GET'])
def current():
    params = request.args

    url = "https://api.spotify.com/v1/me/player/currently-playing"
    try:
        js = make_request(url, params['username'])

        es.index('track', '_doc', id=js['item']['id'], body=js['item'])
        return str(js)
    except Exception as e:
        print(e)
        return "ok"


@app.route('/api/v1/top-artists', methods=['GET'])
def top_artists():
    params = request.args

    url = "https://api.spotify.com/v1/me/top/artists?limit=" + params['limit'] + '&offset=' + params['offset'] + '&time_range=' + params['time']
    js = make_request(url, params['username'])

    for item in js['items']:
        es.index('artist', '_doc', id=item['id'], body=item)

    return str(js)

@app.route('/api/v1/top-tracks', methods=['GET'])
def top_tracks():
    params = request.args

    url = "https://api.spotify.com/v1/me/top/tracks?limit=" + params['limit'] + '&offset=' + params['offset'] + '&time_range=' + params['time']
    js = make_request(url, params['username'])

    for item in js['items']:
        es.index('track', '_doc', id=item['id'], body=item)

    return str(js)


@app.route('/api/v1/saved-albums', methods=['GET'])
def saved_albums():
    params = request.args

    url = "https://api.spotify.com/v1/me/albums?limit=50&offset=" + params['offset']
    js = make_request(url, params['username'])

    for item in js['items']:
        es.index('album', '_doc', id=item['album']['id'], body=item['album'])

    return str(js)

@app.route('/api/v1/saved-tracks', methods=['GET'])
def saved_tracks():
    params = request.args

    url = "https://api.spotify.com/v1/me/tracks?limit=50&offset=" + params['offset']
    js = make_request(url, params['username'])

    for item in js['items']:
        es.index('track', '_doc', id=item['track']['id'], body=item['track'])

    return str(js)


# @app.route('/api/v1/following/<username>', methods=['GET'])
@app.route('/api/v1/following', methods=['GET'])
def following():
    params = request.args

    if 'after' in params:
        url = "https://api.spotify.com/v1/me/following?type=artist&limit=50&after=" + params['after']
    else:
        url = "https://api.spotify.com/v1/me/following?type=artist&limit=50"
    js = make_request(url, params['username'])

    ids = []
    for item in js['artists']['items']:
        es.index('artist', '_doc', id=item['id'], body=item)
        ids.append(item['id'])

    try:
        ids = list(set(get_following(params['username']) + ids))
    except:
        pass
    es.index('following', '_doc', id=params['username'], body={'ids': ids})

    return str(js)


@app.route('/api/v1/new-releases', methods=['GET'])
def new():
    params = request.args

    url = "https://api.spotify.com/v1/browse/new-releases?limit=50&offset=" + params['offset']
    js = make_request(url, params['username'])

    for item in js['albums']['items']:
        es.index('simple-album', '_doc', item, id=item['id'])

    return str(js)


@app.route('/api/v1/recommendations', methods=['GET'])
def recommendations():
    params = request.args

    url = "https://api.spotify.com/v1/recommendations?limit=100&seed_tracks=" + params['seed_tracks']
    js = make_request(url, params['username'])['tracks']

    for item in js:
        es.index('simple-track', '_doc', item, id=item['id'])

    return str(js)


# @app.route('/api/v1/artist-top-tracks', methods=['GET'])
# def artist_top_tracks():
#     params = request.args

#     url = "https://api.spotify.com/v1/artists/" + params['id'] + "/top-tracks?country=US"
#     js = make_request(url, params['username'])

    # ids = []
#     for item in js['tracks']:
#         es.index('track', doc_type='_doc', id=item['id'], body=item)
        # ids.append(item['id'])

# #    es.index('artist-top-tracks', doc_type='_doc', id=params['id'], body={'ids':ids})

#     return str(js)


# @app.route('/api/v1/related', methods=['GET'])
# def related():
#     params = request.args

#     url = "https://api.spotify.com/v1/artists/" + params['id'] + "/related-artists"
#     js = make_request(url, params['username'])

#     ids = []
#     for item in js['artists']:
#         es.index('artist', doc_type='_doc', id=item['id'], body=item)
#         ids.append(item['id'])

#     es.index('related-artists', doc_type='_doc', id=params['id'], body={'ids':ids})

    # return str(js)


app.run(host='0.0.0.0')
# app.run(host='0.0.0.0', port=443, ssl_context='adhoc')
