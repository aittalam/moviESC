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
key_imdb   = 'imdb:#imdbid#'          # the hash containing all the IMDB metadata we are interested in
key_uris   = 'uris:#imdbid#'          # the hash containing all the URIs matching a gived IMDBid
key_hashIMDB = 'h2i:#size#:#hash#'    # cached mappings between bytesize/movhash and IMDB ids
key_genres = 'genre:#genre#'  # the set containing all the IMDBids of movies of a given genre

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
    key_imdb = conf['key_imdb']
    key_uris = conf['key_uris']
    key_hashIMDB = conf['key_hashIMDB']
    key_genres = conf['key_genres']
    redis_host = conf['redis_host']
    redis_port = conf['redis_port']
    redis_db = conf['redis_db']
else:
    logger.error("Could not open config file, reverting to defaults")


def getCachedHash (r,movURL):
    # if the URL has already been cached, load size and hash
    if r.exists(movURL):
        logger.info('Moviehash was cached, skipping hashing (yay!)')
        s = r.hget(movURL,'size')
        h = r.hget(movURL,'hash')
    else:
        logger.info('Moviehash was not cached, hashing URL %s' % movURL)
        # calculate hash
        s,h = im.hashURL(movURL)

        # save data related to URL
        r.hset(movURL,'size',s)
        r.hset(movURL,'hash',h)

    return s,h


def getCachedIMDBid(r, bytesize, movhash):
    # first check if the IMDBid is cached
    key_h2i = conf['key_hashIMDB'].replace("#size#",bytesize).replace("#hash#",movhash)
    IMDBid = r.get(key_h2i)

    if not IMDBid:
        # IMDBid was not cached, try to get it automatically from opensubtitles
        logger.debug('IMDBid was not cached, trying to get it automatically')
        IMDBid = im.getIMDBid(bytesize, movhash)

        # if IMDB cannot be found automatically, ask to provide it manually
        # (but only if interactive mode is enabled)
        if not IMDBid and interactive:
            logger.debug('IMDBid not found, trying to get it manually')
            IMDBid = raw_input("IMDBid not found, please enter it manually: ")

        # if we get it some way, let us save it on Redis
        if IMDBid:
            logger.debug('Caching IMDBid')
            r.set(key_h2i, IMDBid)
    else:
        logger.debug('IMDBid was cached, skipping identification (yay!)')

    return IMDBid

def getCachedMetadata(r, IMDBid):
    IMDBkey = key_imdb.replace("#imdbid#",IMDBid)
    # first check if metadata already exists
    if r.exists(IMDBkey):
        logger.debug('Metadata was cached, skipping download (yay!)')
        m = r.hgetall(IMDBkey)
    else:
        logger.debug('Metadata was not cached, downloading...')
        # if not, get them from IMDB + other APIs (check movieMeta for details)
        m = mm.getMovieMeta(IMDBid,downloadPosters=True)

        if not m:
            logger.error('Could not get IMDB metadata')
            return

        # getMovieMeta should provide everything we need (IMDB meta + something more)
        # we want to save the following keys in the imdb:IMDBid hash
        imdbKeys = ('title', 'q', 'slug', 'year', 'rating', \
                    'runtime_simple', 'plot outline', 'cover url', \
                    'full-size cover url', 'altPosterURL')

        for key in imdbKeys:
            if m.has_key(key):
                r.hsetnx(IMDBkey, key, m[key])
            else:
                logger.warning('Movie with IMDB %s does not have key %s!' %(str(IMDBid),key))

        # movie genres
	    for genre in m.get('genres',[]):
		    r.sadd(key_genres.replace("#genre#",genre), IMDBid)

        # poster URLs
        # TODO: fix key names here
        # I like the fact that posters: key are agnostic of the poster provenance,
        # but you know nothing about quality etc! Probably it is better to save
        # poster URLs together with imdb:* keys, keeping their original semantics
        # related to size/quality
        if m.has_key('full-size cover url'):
    	    r.sadd('posters:'+IMDBid,m['full-size cover url'])
        if m.has_key('altPosterURL'):
    	    r.sadd('posters:'+IMDBid,m['altPosterURL'])

    return m


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
    s,h = getCachedHash(r,movURL)

    # if an error occurred in hashing, skip URL and save it in failed
    if not s:
        r.sadd(key_failed, movURL)
        continue

    # get IMDB id from opensubtitles
    logger.debug("Getting IMDBid for movie (%s,%s)" %(str(s),str(h)))
    IMDBid = getCachedIMDBid(r,s,h)

    # if the URL was not available (or cannot be retrieved), skip it and save it in failed
    if not IMDBid:
        r.sadd(key_noIMDB, movURL)
        continue

    # if you got the IMDB id, save it together with the URL
    logger.info("IMDBid found! Saving URL for IMDBid %s" %str(IMDBid))
    r.sadd(key_uris.replace("#imdbid#",IMDBid), movURL)

    # add metadata
    logger.debug("Getting movie metadata for IMDBid %s" %str(IMDBid))
    m = getCachedMetadata(r,IMDBid)

    if not m:
        # TODO: should have a key_noMETA instead
        r.sadd(key_noIMDB,movURL)
        continue

    logger.info("Metadata found for IMDBid %s" %str(IMDBid))

    movnum = r.scard(key_toIndex)

logger.info("Movie queue empty: stopping.")
