import init
import sys
from trivialScraper import getAndExtract
import imdb
import urllib
import re
import md5
import os, os.path

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
def getMovieMeta(IMDBid, downloadPosters = False):
    logger.debug('Getting movie metadata from IMDB')
    try:
        m = ia.get_movie(IMDBid)

        # -------------------------------------------------------
        # clean runtime (as it is a list, just get first element)
        # if key does not exist, just provide 0 as runtime
        m['runtime_simple'] = m.get('runtime',[u'0'])[0]

        # -------------------------------------------------------
        # generate slug:
        # (1) lowercase long imdb title
        slug = m.get('long imdb title','').lower()
        # remove anything which is not alphanumeric or a space
        slug = re.sub('[^a-zA-Z0-9 ]','',slug)
        # convert spaces into dashes
        m['slug'] = re.sub(' ','-',slug)

        # -------------------------------------------------------
        # add alternative poster URL if it exists
        #altPosterURL = getPosterURL(IMDBid)
        #if altPosterURL:
        #    m['altPosterURL'] = altPosterURL

        # -------------------------------------------------------
        # download posters
        if downloadPosters:
            logger.debug('Storing posters in %s' % conf['path_posters'])
            for posterKey in ('full-size cover url','altPosterURL'):
                if m.has_key(posterKey):
                    # build filename as a hash of the URL
                    fname = os.path.join(conf['path_posters'],md5.new(m[posterKey]).hexdigest())
                    # check if file exists...
                    if os.path.isfile(fname):
                        logger.debug('Poster at %s has already been downloaded: skipping' % m[posterKey])
                    else:
                        logger.debug('Downloading poster file at url %s' % m[posterKey])
                        # if not, download and save poster
                        # TODO: catch urllib exceptions here (see below some for urllib2)
                        urllib.urlretrieve(m[posterKey],fname)
        return m
    except imdb.IMDbDataAccessError, e:
        logger.error('IMDB Data Access Error: %s' % e.errmsg)
        return
#    except urllib2.HTTPError, e:
#        logger.error('HTTPError = ' + str(e.code))
#    except urllib2.URLError, e:
#        logger.error('URLError = ' + str(e.reason))
#    except httplib.HTTPException, e:
#        logger.error('HTTPException')
#    except:
#        logger.error('Unknown exception while downloading poster')

if __name__ == '__main__':

    if len(sys.argv)<2:
        IMDBid = "3268458"
    else:
        IMDBid = sys.argv[1]

    print "[i] Getting metadata for IMDB id %s..." % IMDBid
    m = getMovieMeta(IMDBid)

    if m:
        # choose which keys we want printed (e.g. ignoring binaries)
        imdbKeys = ('title', 'long imdb title', 'slug', 'year', 'rating', \
            'runtime_simple', 'plot outline', 'cover url', 'full-size cover url', \
            'altPosterURL')
        for key in imdbKeys:
            print "  %s: %s" % (key, m.get(key,""))

        # movie genres
        print "  Genres:",
        for genre in m.get('genres',[]):
            print "%s" %genre,

    else:
        print "[x] No metadata found"
