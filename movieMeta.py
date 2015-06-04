import init
import sys
from trivialScraper import getAndExtract
import imdb

conf,logger = init.configure()
if conf is None:
    logger.error("Could not open config file, reverting to defaults")

URL_MP_MOVIE = 'http://www.movieposterdb.com/movie/'
URL_MP_POSTER = 'http://www.movieposterdb.com/poster/'
RE_MP_POSTER = 'id="poster_([^"]+)"[^>]+width: 310'
RE_MP_IMG = 'property="og:image" content="([^"]+)"'

ia = imdb.IMDb()

def getPosterURL(IMDBid):
    logger.debug('Getting alternative poster URL from movieposterdb')
    # get a poster page (the bigger/main one) from movieposterdb
    m = getAndExtract(URL_MP_MOVIE + str(IMDBid), RE_MP_POSTER)
    if not m :
        logger.error('Could not get poster page from movieposterdb')
        return
    # get the actual poster image URL from the poster page
    m = getAndExtract(URL_MP_POSTER + str(m.group(1)), RE_MP_IMG)
    if not m :
        logger.error('Could not get poster URL from movieposterdb')
        return
    # return the URL
    return m.group(1)

# getMovieMeta gets movie metadata from IMDB given the ID
# might be extended to something smarter
def getMovieMeta(IMDBid):
    logger.debug('Getting movie metadata from IMDB')
    try:
        m = ia.get_movie(IMDBid)
        altPosterURL = getPosterURL(IMDBid)
        if altPosterURL:
            m['altPosterURL'] = altPosterURL
        return m
    except imdb.IMDbDataAccessError, e:
        logger.error('IMDB Data Access Error: %s' % e.errmsg)
        return

if __name__ == '__main__':

    if len(sys.argv)<2:
        IMDBid = "3268458"
    else: 
        IMDBid = sys.argv[1]
	
    print "[i] Getting metadata for IMDB id %s..." % IMDBid
    m = getMovieMeta(IMDBid)

    if m:
        if m.has_key('title'):
            print "    Title: %s" %m['title']
    if m.has_key('year'):
            print "    Year: %s" %m['year']
    if m.has_key('rating'):
            print "    Rating: %s" %m['rating']
    if m.has_key('plot outline'):
            print "    Plot Outline: %s" %m['plot outline']

    # poster URLs
    if m.has_key('full-size cover url'):
            print "    Cover URL: %s " %m['full-size cover url']
    if m.has_key('altPosterURL'):
            print "    Alt Poster URL: %s " %m['altPosterURL']

    # movie genres
    if m.has_key('genres'):
        print "    Genres:",
        for genre in m['genres']:
            print " %s" %genre,

    else:
        print "[x] No metadata found"
