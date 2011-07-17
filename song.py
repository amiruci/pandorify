class Song(object):
    """TODO(amir): rename this to PandoraSong?"""
    def __init__(self, title, artist, album_art_url):
        self.title = title
        self.artist = artist
        self.album_art_url = album_art_url

    def __str__(self):
        return self.title + ' by ' + self.artist + ' - ' + self.album_art_url
