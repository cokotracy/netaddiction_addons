import urllib2

from tempfile import TemporaryFile
from ftplib import FTP


class Downloader(object):
    def encode(self, source):
        return unicode(source, errors='ignore')

    def download(self):
        raise NotImplementedError()


class FTPDownloader(Downloader):
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password

    def _download(self, path):  # TODO togliere underscore
        tempfile = TemporaryFile()

        ftp = FTP(self.hostname)
        ftp.login(self.username, self.password)
        ftp.set_pasv(True)
        ftp.retrbinary('RETR %s' % path, tempfile.write)
        ftp.quit()

        tempfile.seek(0)
        source = tempfile.read()
        tempfile.close()

        return self.encode(source)

    def download(self, path):  # TODO togliere metodo
        import os

        basename = os.path.basename(path)
        filename = '/tmp/%s' % basename

        if not os.path.exists(filename):
            content = self._download(path)

            with open(filename, 'w') as f:
                f.write(content)
        else:
            with open(filename) as f:
                content = f.read()

        return content


class HTTPDownloader(Downloader):
    def __init__(self, body=None, headers={}):
        self.body = body
        self.headers = headers

    def download(self, url, raw=False):
        request = urllib2.Request(url, self.body)

        for key, value in self.headers.items():
            request.add_header(key, value)

        response = urllib2.urlopen(request)
        source = response.read()

        if raw:
            return source

        return self.encode(source)
