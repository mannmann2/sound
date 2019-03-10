"https://api.spotify.com/v1/me"
@app.route('/api/v1/login', methods=['GET'])
@app.route('/api/v1/user', methods=['GET'])

"https://api.spotify.com/v1/audio-analysis/{id}"
@app.route('/api/v1/analysis', methods=['GET'])

"https://api.spotify.com/v1/audio-features"
@app.route('/api/v1/features', methods=['GET'])

"https://api.spotify.com/v1/search"
@app.route('/api/v1/search', methods=['GET'])

"https://api.spotify.com/v1/me/player/recently-played"
@app.route('/api/v1/recently-played', methods=['GET'])

"https://api.spotify.com/v1/me/player/currently-playing"
@app.route('/api/v1/currently-playing', methods=['GET'])

"https://api.spotify.com/v1/me/top/artists"
@app.route('/api/v1/top-artists', methods=['GET'])

"https://api.spotify.com/v1/me/top/tracks"
@app.route('/api/v1/top-tracks', methods=['GET'])

"https://api.spotify.com/v1/me/albums"
@app.route('/api/v1/saved-albums', methods=['GET'])

"https://api.spotify.com/v1/me/tracks"
@app.route('/api/v1/saved-tracks', methods=['GET'])

"https://api.spotify.com/v1/me/following?type=artist" #
@app.route('/api/v1/following', methods=['GET'])

"https://api.spotify.com/v1/browse/new-releases"
@app.route('/api/v1/new-releases', methods=['GET'])

"https://api.spotify.com/v1/recommendations"
@app.route('/api/v1/recommendations', methods=['GET'])

#artists
# "https://api.spotify.com/v1/artists/{id}/related-artists"
# @app.route('/api/v1/related', methods=['GET'])

# "https://api.spotify.com/v1/artists/{id}/top-tracks"
# @app.route('/api/v1/artist_top', methods=['GET'])

#albums
