import redis

# connect to redis
r = redis.StrictRedis(host='localhost',port='6379', db=0)

movies = r.keys("posters:*")

print '<html><head><title>MovieZzZzZz!!!</title><link rel="stylesheet" type="text/css" href="movies.css"></head><body><div><ul>'

for movie in movies:
	IMDBid = movie.replace("posters:","")
	posterURL = r.smembers(movie).pop()
	movieURL = r.smembers("urls:"+IMDBid).pop()
	movieTitle = r.hget("imdb:"+IMDBid,"title")
	if not movieTitle:
		movieTitle=""

	print '<li><a href="'+movieURL+'"><img src="'+posterURL+'" alt="'+movieTitle+'"></a></li>'

print '</ul></div></body></html>'
