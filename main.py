import logging
import os
import urllib2

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from xml.dom import minidom 

class Song(object):
    def __init__(self, title, artist, album_art_url):
        self.title = title
        self.artist = artist
        self.album_art_url = album_art_url

    def __str__(self):
        return self.title + ' by ' + self.artist + ' - ' + self.album_art_url


class MainPage(webapp.RequestHandler):
    def get(self):
        template_values = {}
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))


class Pandorify(webapp.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        url = self.request.get('url').strip()
        usock = urllib2.urlopen(url) 
        xmldoc = minidom.parse(usock) 
        usock.close()
        #<rss xmlns:pandora="http://www.pandora.com/rss/1.0/modules/pandora/" 
        #     xmlns:mm="http://musicbrainz.org/mm/mm-2.1#" version="2.0">
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
            self.response.out.write(song)

application = webapp.WSGIApplication(
                                    [('/', MainPage),
                                     ('/pandorify', Pandorify)],
                                     debug=True)



def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
