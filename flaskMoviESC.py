import init
from flask import Flask, jsonify, abort, send_file
import redis
import urllib
import StringIO

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
        mov  = r.keys('postersIMG:*')
        for m in mov :
            IMDBid = m.replace("postersIMG:","")
            movieURL = r.smembers("urls:"+IMDBid).pop()
            movieTitle = r.hget("imdb:"+IMDBid,"title")
            if not movieTitle:
                movieTitle=""

            movList = movList + '<li><a href="%s"><img src="/api/v1.0/poster/%s" alt="%s"></a></li>\n' %(movieURL, IMDBid, movieTitle)

        return html.replace('###MOVIELIST###',movList)


# get urls from IMDB ids
@app.route('/api/v1.0/urls/<string:IMDBid>', methods = ['GET'])
def get_urls(IMDBid):

	urls = list(r.smembers("urls:"+str(IMDBid)))

    	# return the full data back
    	return jsonify( { 'urls': urls } )

# get (a list of) poster urls from IMDB ids
@app.route('/api/v1.0/posters/<string:IMDBid>', methods = ['GET'])
def get_posters(IMDBid):

	posters = list(r.smembers("posters:"+str(IMDBid)))

    	# return the full data back
    	return jsonify( { 'posters': posters } )


# get (a single, randomly chosen) poster image for a given IMDBid
@app.route('/api/v1.0/poster/<string:IMDBid>', methods = ['GET'])
def get_poster(IMDBid):
    binary_image = r.srandmember('postersIMG:'+IMDBid)
    return send_file(StringIO.StringIO(binary_image), mimetype='image/jpg')


# get IMDBs from genres
@app.route('/api/v1.0/genre/<string:genres>', methods = ['GET'])
def get_IMDBids(genres):
        genreList = str.split(urllib.unquote_plus(genres).encode())

        IMDBids = list(r.sinter(map(lambda x:'genre:'+str(x),set(genreList))))

    	# return the full data back
    	return jsonify( { 'IMDBids': IMDBids} )

# get details from IMDB id
@app.route('/api/v1.0/details/<string:IMDBid>', methods = ['GET'])
def get_details(IMDBid):

        details = r.hgetall("imdb:"+str(IMDBid))

    	# return the full data back
    	return jsonify( { 'details': details} )


# get all data about an IMDB id
@app.route('/api/v1.0/data/<string:IMDBid>', methods = ['GET'])
def get_all_details(IMDBid):

        details = r.hgetall("imdb:"+str(IMDBid))
	urls = list(r.smembers("urls:"+str(IMDBid)))
	posters = list(r.smembers("posters:"+str(IMDBid)))

    	# return the full data back
    	return jsonify( { 'details': details, 'urls': urls, 'posters': posters} )

# get all data about an IMDB id in HTML
@app.route('/api/v1.0/html/<string:IMDBid>', methods = ['GET'])
def get_html_details(IMDBid):

    details = r.hgetall("imdb:"+str(IMDBid))
    urls = list(r.smembers("urls:"+str(IMDBid)))
    posters = list(r.smembers("posters:"+str(IMDBid)))

    if details:
        html = '<html><head><title>'+details['title']+'</title></head><body>'
        html += '<a href="http://www.imdb.com/title/tt'+IMDBid+'">back</a><br/>'
        html += '<h1>'+details['title']
        if details.has_key('year'):
            html += ' ('+details['year']+')'
        html += '</h1>'
        if details.has_key('rating'):
            html += 'Rating: ' + details['rating'] + '/10<br/><br/>'
        html += '<img src="/api/v1.0/poster/'+IMDBid+'"><br/>'
        if details.has_key('plot'):
            html += '<i>'+details['plot']+'</i><br/>'
        html += '<br/>Download links:<br/><ul>'
        for url in urls:
            html += '<li><a href="'+url+'">'+url+'</a></li>'
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
	IMDBids = r.keys("imdb:*")
	for IMDBid in IMDBids:
		IMDBid = IMDBid.replace("imdb:","")
		details = r.hgetall("imdb:"+str(IMDBid))
        	urls = list(r.smembers("urls:"+str(IMDBid)))
        	posters = list(r.smembers("posters:"+str(IMDBid)))
		everything.append({ 'IMDBid': IMDBid, 'details': details, 'urls': urls, 'posters': posters})
	
        # return the full data back
        return jsonify( { 'count': len(IMDBids), 'movies': everything})


if __name__ == "__main__":

    # connect to redis
    r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)

    if devel :
        app.debug = True
        app.run(host='0.0.0.0')
    else :   
        # change with the following when in production mode
        app.debug = False
        app.run(host='0.0.0.0')
