import init
from flask import Flask, jsonify, abort, send_file
import redis
import urllib
import io
import os
import hashlib

showMoviesTemplate = './html/movies.html'

devel = True # set to False when you bring this script into production
app = Flask(__name__)

# default parameters for redis connection, will be overridden by the config file
redis_host = 'localhost'
redis_port = '6379'
redis_db = '0'

# load configuration params and start logger
# (just use default config.yaml filename for now, might extend to a parameter later)
conf,logger = init.configure(loggerName='movies')
if conf is not None:
    redis_host = conf['redis_host']
    redis_port = conf['redis_port']
    redis_db = conf['redis_db']
else:
    logger.error("Could not open config file, reverting to defaults")


# just a placeholder - modify before releasing
@app.route("/")
def showMovies():
    f = open(showMoviesTemplate, 'r')
    html = f.read()
    f.close()

    movList = ''
    # get only the movies which have at least a poster image?
    key_uris = conf['key_uris']
    mov  = r.keys(key_uris.replace('#imdbid#','*'))
    for m in mov :
        IMDBid = m.replace(key_uris.replace('#imdbid#',''),'')
        movieURL = r.smembers(key_uris.replace('#imdbid#',IMDBid)).pop()
        movieTitle = r.hget(conf['key_imdb'].replace('#imdbid#',IMDBid),'long imdb title')
        if not movieTitle:
            movieTitle=""

        movList = movList + '<li><a href="%s"><img src="/api/v1.0/poster/%s" alt="%s"></a></li>\n' %(movieURL, IMDBid, movieTitle)

    return html.replace('###MOVIELIST###',movList)


# get urls from IMDB ids
@app.route('/api/v1.0/uris/<string:IMDBid>', methods = ['GET'])
def get_uris(IMDBid):
    uris = list(r.smembers(conf['key_uris'].replace('#imdbid#',IMDBid)))

    # return the full data back
    return jsonify( { 'uris': uris } )


# get (a list of) poster urls from IMDB ids
@app.route('/api/v1.0/posters/<string:IMDBid>', methods = ['GET'])
def get_posters(IMDBid):
    posters = list(r.smembers("posters:"+str(IMDBid)))

    # return the full data back
    return jsonify( { 'posters': posters } )


# get (a single, randomly chosen) poster image for a given IMDBid
@app.route('/api/v1.0/poster/<string:IMDBid>', methods = ['GET'])
def get_poster(IMDBid):
    # TODO: remove this (low effort, but not very useful), and prefer something like poster-large, poster-medium, etc.
    #       within the imdb:* keys. Until then, the "posters" key might remain unofficial
    posterURL = r.srandmember('posters:'+IMDBid)
    fname = os.path.join(conf['path_posters'],hashlib.new('md5', posterURL.encode()).hexdigest())
    # TODO: check for filename existence first - if not, choose default "poster missing" pic
    f = open(fname,'rb')
    image = send_file(io.BytesIO(f.read()), mimetype='image/jpg')
    f.close()
    return image


# get genres list
@app.route('/api/v1.0/genres/', methods = ['GET'])
def get_genres():
    genreList = r.keys(conf['key_genres'].replace('#genre#','*'))

    # return the full data back
    return jsonify( { 'genres': genreList} )


# get IMDBs from genres
@app.route('/api/v1.0/genre/<string:genres>', methods = ['GET'])
def get_IMDBids(genres):
    genreList = str.split(urllib.unquote_plus(genres).encode())

    IMDBids = list(r.sinter(map(lambda x:conf['key_genres'].replace('#genre#',str(x)),set(genreList))))

    # return the full data back
    return jsonify( { 'IMDBids': IMDBids} )


# get details from IMDB id
@app.route('/api/v1.0/details/<string:IMDBid>', methods = ['GET'])
def get_details(IMDBid):
    details = r.hgetall(conf['key_imdb'].replace('#imdbid#',IMDBid))

    # return the full data back
    return jsonify( { 'details': details} )


# get all data about an IMDB id
@app.route('/api/v1.0/data/<string:IMDBid>', methods = ['GET'])
def get_all_details(IMDBid):
    details = r.hgetall(conf['key_imdb'].replace('#imdbid#',IMDBid))
    urls = list(r.smembers(conf['key_uris'].replace('#imdbid#',IMDBid)))
    posters = list(r.smembers("posters:"+str(IMDBid)))

    # return the full data back
    return jsonify( { 'details': details, 'urls': urls, 'posters': posters} )


# get all data about an IMDB id in HTML
@app.route('/api/v1.0/html/<string:IMDBid>', methods = ['GET'])
def get_html_details(IMDBid):
    details = r.hgetall(conf['key_imdb'].replace('#imdbid#',IMDBid))
    urls = list(r.smembers(conf['key_uris'].replace('#imdbid#',IMDBid)))
    posters = list(r.smembers("posters:"+str(IMDBid)))

    if details:
        html = '<html><head><title>%s</title></head><body>' % details['long imdb title']
        html += '<a href="http://www.imdb.com/title/tt%s">back</a><br/>' % IMDBid
        html += '<h1>%s</h1>' % details['long imdb title']
        if 'rating' in details:
            html += 'Rating: %s/10<br/><br/>' % details['rating']
        html += '<img src="/api/v1.0/poster/%s"><br/>' % IMDBid
        if 'plot' in details:
            html += '<i>%s</i><br/>' % details['plot']
        html += '<br/>Download links:<br/><ul>'
        for url in urls:
            html += '<li><a href="%s">%s</a></li>' %(url,url)
        html += '</ul>'
        html += '</body></html>'
    else:
        html = '<html><head><title>No links found</title></head><body>'
        html += 'No links found for the movie. Please grow your index!'
        html += '</body></html>'
    # return the full data back
    return html


# get everything!
@app.route('/api/v1.0/all', methods = ['GET'])
def get_everything():

    everything=[]
    IMDBids = r.keys(conf['key_imdb'].replace('#imdbid#','*'))
    for IMDBid in IMDBids:
        IMDBid = IMDBid.replace(conf['key_imdb'].replace('#imdbid#',''),"")
        details = r.hgetall(conf['key_imdb'].replace('#imdbid#',IMDBid))
        urls = list(r.smembers(conf['key_uris'].replace('#imdbid#',IMDBid)))
        posters = list(r.smembers("posters:"+str(IMDBid)))
        everything.append({ 'IMDBid': IMDBid, 'details': details, 'urls': urls, 'posters': posters})

        # return the full data back
        return jsonify( { 'count': len(IMDBids), 'movies': everything})


if __name__ == "__main__":

    # connect to redis
    r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)

    if devel :
        app.debug = True
        app.run(host='0.0.0.0')
    else :
        # change with the following when in production mode
        app.debug = False
        app.run(host='0.0.0.0')
