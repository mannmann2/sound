def day(users):
    body = {
        "query": {
            "bool": {"must": {
                "range": {
                    "played_at": {"gte": "now-24h/h", "lte": "now/h"}
                }},
                "filter": {"match": {"played_by": users}}
            }
        },
        "size": 0,
        "aggs": {
            "artists": {"terms": {"field": "track.artists.name.keyword",
                                  "size": 42}},
            "tracks": {"terms": {"field": "track.name.keyword",
                                 "size": 42}},
        }
    }
    return body

def week(users):
    body = {
        "query": {
            "bool": {"must": {
                "range": {
                    "played_at": {"gte": "now-7d/d", "lte": "now/d"}
                }},
                "filter": {"match": {"played_by": users}}
            }
        },
        "size": 0,
        "aggs": {
            "artists": {"terms": {"field": "track.artists.name.keyword",
                                  "size": 42}},
            "tracks": {"terms": {"field": "track.name.keyword",
                                 "size": 42}},
        }
    }
    return body
