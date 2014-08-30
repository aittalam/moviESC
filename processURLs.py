import redis
import identifyMovie
from imdb import IMDb

# move this setting to a configuration / command line parameter
interactive = False

# connect to redis
r = redis.StrictRedis(host='localhost',port='6379', db=0)
ia = IMDb()

key_toIndex = 'toIndex'
key_failed = 'failed'
key_noIMDB = 'noIMDB'

movnum = r.scard(key_toIndex)

# while you have stuff to index
while movnum > 0:
	movURL = r.spop(key_toIndex)

	if not movURL:
		print "Done."
		break
		
	# calculate hash
	print "Hashing URL " + movURL + "... ",
	s,h = identifyMovie.hashURL(movURL)
	print "ok"

	# if an error occurred in hashing, skip URL and save it in failed
	if not s:
		r.sadd(key_failed, movURL)
		continue

	# save data related to URL
	r.hset(movURL,'size',s)
	r.hset(movURL,'hash',h)

	# get IMDB id from opensubtitles
	print "Getting IMDB id for movie... ",
	IMDBid = identifyMovie.getIMDBid(s,h)
	print "ok"

	# if the URL was not avaiable (or cannot be retrieved), skip it and save it in failed
        if not IMDBid and interactive:
                IMDBid = raw_input("IMDBid not found, please enter it manually: ")

	if not IMDBid:
		r.sadd(key_noIMDB, movURL)
		continue

	# if you got the IMDB id, save it together with the URL
	print "Saving in Redis... ",
	r.sadd("urls:"+IMDBid, movURL)
	print "ok"

	# add metadata
	print "Getting movie metadata... ",
	try:
		m = ia.get_movie(IMDBid)
	except IMDbDataAccessError, e:
		print '[x] IMDB Data Access Error: %s' % e.errmsg
		r.sadd(key_noIMDB, movURL)
		continue

	# string metadata (title, year, summary)
	# should we suppose we have at least the title?
	if m.has_key('title'):
		r.hsetnx("imdb:"+IMDBid,'title',m['title'])
	if m.has_key('year'):
		r.hsetnx("imdb:"+IMDBid,'year',m['year'])
	if m.has_key('rating'):
		r.hsetnx("imdb:"+IMDBid,'rating',m['rating'])
	if m.has_key('plot outline'):
		r.hsetnx("imdb:"+IMDBid,'plot',m['plot outline'])

	# poster URLs
	if m.has_key('cover url'):
		r.sadd('posters:'+IMDBid,m['cover url'])

	altPosterURL = identifyMovie.getPosterURL(IMDBid)
	if altPosterURL:
		r.sadd('posters:'+IMDBid,altPosterURL)

	# movie genres
	if m.has_key('genres'):
		for genre in m['genres']:
			r.sadd('genre:'+genre,IMDBid)

	print "ok"
	movnum = r.scard(key_toIndex)
