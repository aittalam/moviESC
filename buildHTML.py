import init
import redis

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

# connect to redis
logger.info("Reading data from Redis (%s:%s, db %s)" %(redis_host,redis_port,redis_db))
r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)

movies = r.keys("posters:*")

print ('<html><head><title>MovieZzZzZz!!!</title><link rel="stylesheet" type="text/css" href="movies.css"></head><body><div><ul>')

for movie in movies:
	IMDBid = movie.replace("posters:","")
	posterURL = r.smembers(movie).pop()
	movieURL = r.smembers("uris:"+IMDBid).pop()
	movieTitle = r.hget("imdb:"+IMDBid,"title")
	if not movieTitle:
		movieTitle=""

	print ('<li><a href="'+movieURL+'"><img src="'+posterURL+'" alt="'+movieTitle+'"></a></li>')

print ('</ul></div></body></html>')
