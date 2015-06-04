import init
import redis
import identifyMovie as im
import movieMeta as mm

# default, hardcoded values for some settings (you can override them in the config file)

# if movie identification is interactive, then whenever a movie cannot be identified 
# the IMDB id is asked to the user on the command line
interactive = False         
key_toIndex = 'toIndex'     # the queue (actually a set now) where the movies that still need to be indexed are stored
key_failed = 'failed'       # the set where the unreadable (no size/hash) movies are saved 
key_noIMDB = 'noIMDB'       # the set containing the movies for which no IMDB was found

# default parameters for redis connection
redis_host = 'localhost'
redis_port = '6379'
redis_db = '0'

# load configuration params and start logger
# (just use default config.yaml filename for now, might extend to a parameter later)
conf,logger = init.configure()
if conf is not None:
    interactive = conf['interactive_ident']
    key_toIndex = conf['key_toIndex']
    key_failed = conf['key_failed']
    key_noIMDB = conf['key_noIMDB']
    redis_host = conf['redis_host']
    redis_port = conf['redis_port']
    redis_db = conf['redis_db']
else:
    logger.error("Could not open config file, reverting to defaults")


# connect to redis
logger.info("Storing URLs in Redis (%s:%s, db %s)" %(redis_host,redis_port,redis_db))
r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)

movnum = r.scard(key_toIndex)

# while you have stuff to index
while movnum > 0:
    movURL = r.spop(key_toIndex)

    # some other thread might have popped the last url from the queue
    if not movURL:
        break

    logger.info("Identifying URL " + movURL)

    # calculate hash
    logger.debug("Hashing URL " + movURL)
    s,h = im.hashURL(movURL)

    # if an error occurred in hashing, skip URL and save it in failed
    if not s:
        r.sadd(key_failed, movURL)
        continue

    # save data related to URL
    r.hset(movURL,'size',s)
    r.hset(movURL,'hash',h)

    # get IMDB id from opensubtitles
    logger.debug("Getting IMDBid for movie (%s,%s)" %(str(s),str(h)))
    IMDBid = im.getIMDBid(s,h)

    # if the URL was not available (or cannot be retrieved), skip it and save it in failed
    if not IMDBid and interactive:
        IMDBid = raw_input("IMDBid not found, please enter it manually: ")

    if not IMDBid:
        r.sadd(key_noIMDB, movURL)
        continue

    # if you got the IMDB id, save it together with the URL
    logger.info("IMDBid found! Saving URL for IMDBid %s" %str(IMDBid))
    r.sadd("urls:"+IMDBid, movURL)

    # add metadata
    logger.debug("Getting movie metadata for IMDBid %s" %str(IMDBid))
    m = mm.getMovieMeta(IMDBid)
    if not m:
        r.sadd(key_noIMDB,movURL)
        continue

    logger.info("Metadata found for IMDBid %s" %str(IMDBid))
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
    if m.has_key('altPosterURL'):
	    r.sadd('posters:'+IMDBid,m['altPosterURL'])

    # movie genres
    if m.has_key('genres'):
	    for genre in m['genres']:
		    r.sadd('genre:'+genre,IMDBid)

    movnum = r.scard(key_toIndex)

logger.info("Movie queue empty: stopping.")
