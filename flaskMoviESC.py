from flask import Flask, jsonify, abort
import redis
import urllib
import argparse

devel = True # set to False when you bring this script into production
app = Flask(__name__)


# just a placeholder - modify before releasing
@app.route("/")
def hello():
    return "Hello World!\n\n"

# get urls from IMDB ids
@app.route('/api/v1.0/urls/<string:IMDBid>', methods = ['GET'])
def get_urls(IMDBid):

	urls = list(r.smembers("urls:"+str(IMDBid)))

    	# return the full data back
    	return jsonify( { 'urls': urls } )

# get poster urls from IMDB ids
@app.route('/api/v1.0/urls/<string:IMDBid>', methods = ['GET'])
def get_posters(IMDBid):

	posters = list(r.smembers("posters:"+str(IMDBid)))

    	# return the full data back
    	return jsonify( { 'posters': posters } )

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
	r = redis.StrictRedis(host='localhost',port='6379', db=0)

	if devel :
		app.debug = True
		#app.run()
		app.run(host='0.0.0.0')
	else :   
		# change with the following when in production mode
		app.debug = False
		app.run(host='0.0.0.0')
