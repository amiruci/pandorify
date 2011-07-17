import logging
import os
import urllib2

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from xml.dom import minidom 


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
        self.response.out.write(xmldoc.toxml())

application = webapp.WSGIApplication(
                                    [('/', MainPage),
                                     ('/pandorify', Pandorify)],
                                     debug=True)



def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
