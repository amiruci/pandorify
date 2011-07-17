import json
import logging
import os
import urllib2

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
    def post(self):
        url = self.request.get('url').strip()
        usock = urllib2.urlopen(url) 
        xmldoc = minidom.parse(usock) 
        usock.close()
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
            song = Song(track_title, artist_title, url)
            songs.append(song)

        # Just query for 3 songs to avoid 503s :/
        songs = songs[:3]
        for song in songs:
            spotify_query = 'http://ws.spotify.com/search/1/track.json?q=' + song.artist + ' ' + song.title
            spotify_query_result = urllib2.urlopen(spotify_query)
            json_result = json.loads(spotify_query_result.read())
            tracks = json_result.get('tracks', {})
            if not tracks:
                self.response.out.write('Nothing found for "'+spotify_query+'" :(')
                continue
            self.response.out.write('<a href="'+tracks[0]['href']+'">' + tracks[0]['name'] + ' by ' + tracks[0]['artists'][0]['name'] + '</a> for query "'+ song.artist + ' ' + song.title+'"<hr>')


class SpotifySearcher(webapp.RequestHandler):
    def get(self):
        try:
            query = self.request.get('q').strip()
            result = urllib2.urlopen('http://ws.spotify.com/search/1/track.json?q='+query)
            json_result = json.loads(result.read())
            tracks = json_result.get('tracks', {})
            if not tracks:
                self.response.out.write('Nothing found for "'+query+'" :(')
                return
            self.response.out.write('Showing results for "'+query+'"<br><br>')
            for track in tracks:
                self.response.out.write('<a href="'+track['href']+'">' + track['name'] + ' by ' + track['artists'][0]['name'] + '</a><hr>')
            
        except urllib2.URLError, e:
            logging.error(e)
            self.response.out.write(e)


application = webapp.WSGIApplication(
                                    [('/', MainPage),
                                     ('/search', SpotifySearcher),
                                     ('/pandorify', Pandorify)],
                                     debug=True)



def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
