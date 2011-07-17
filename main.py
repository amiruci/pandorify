import json
import logging
import os
import urllib2

from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from song import Song
from xml.dom import minidom 


class MainPage(webapp.RequestHandler):
    def get(self):
        template_values = {}
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))


class Pandorify(webapp.RequestHandler):
    
    spotify_song_query_template = 'http://ws.spotify.com/search/1/track.json?q=%(artist)s %(title)s'
    
    def post(self):
        url = self.request.get('url').strip()
        usock = urllib2.urlopen(url) 
        xmldoc = minidom.parse(usock) 
        usock.close()
        songs = self.getSongsFromXmlDocument(xmldoc)
        for song in songs:
            spotify_song_query = Pandorify.spotify_song_query_template % {'artist': song.artist, 'title': song.title}
            try:
                spotify_query_result = urlfetch.fetch(spotify_song_query, method=urlfetch.GET, deadline=10)
            except urllib2.URLError, e:
                logging.error(e)
                self.response.out.write('%(error_code)s for %(query)s :(<hr>' % {'error_code': spotify_query_result.status_code, 'query': spotify_song_query})
                continue
            if spotify_query_result.status_code != 200:
                self.response.out.write('%(error_code)s for %(query)s :(<hr>' % {'error_code': spotify_query_result.status_code, 'query': spotify_song_query})
                continue
        
            json_result = json.loads(spotify_query_result.content)
            tracks = json_result.get('tracks', {})
            if tracks:
                # Select the first track for now
                # TODO(amir): be smart about which track you select
                track = tracks[0]
                self.response.out.write('<a href="%(url)s">%(title)s by %(artist)s</a> for query "%(query)s"<hr>' %
                                        {'url': track['href'], 'title':  track['name'], 'artist': track['artists'][0]['name'], 'query': song.artist + ' ' + song.title})
            else:
                self.response.out.write('Nothing found for "%s" :(<hr>' % spotify_song_query)

    def getSongsFromXmlDocument(self, xmldoc):
        # <rss xmlns:pandora="http://www.pandora.com/rss/1.0/modules/pandora/" 
        # xmlns:mm="http://musicbrainz.org/mm/mm-2.1#" version="2.0">
        pandora_ns_uri = xmldoc.childNodes[0].attributes['xmlns:pandora'].nodeValue
        mm_ns_uri = xmldoc.childNodes[0].attributes['xmlns:mm'].nodeValue
        dc_ns_uri = xmldoc.childNodes[0].attributes['xmlns:dc'].nodeValue
        items = xmldoc.getElementsByTagName('item')
        
        songs = []
        for item in items:
            # <mm:Track>
            # <dc:title>I Remember (Instrumental)</dc:title>
            # <mm:trackNum>3</mm:trackNum>
            # </mm:Track>
            track = item.getElementsByTagNameNS(mm_ns_uri, 'Track')[0]
            track_title = track.getElementsByTagNameNS(dc_ns_uri, 'title')[0].firstChild.data
            artist = item.getElementsByTagNameNS(mm_ns_uri, 'Artist')[0]
            artist_title = artist.getElementsByTagNameNS(dc_ns_uri, 'title')[0].firstChild.data
            url = item.getElementsByTagNameNS(pandora_ns_uri, 'albumArtUrl')[0].firstChild.data
            songs.append(Song(track_title, artist_title, url))
        return songs


application = webapp.WSGIApplication(
                                    [('/', MainPage),
                                     ('/pandorify', Pandorify)],
                                     debug=True)


def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
