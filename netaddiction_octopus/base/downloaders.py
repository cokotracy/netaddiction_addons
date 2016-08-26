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

    def download(self, path):
        tempfile = TemporaryFile()

        ftp = FTP(self.hostname)
        ftp.login(self.username, self.password)
        ftp.set_pasv(True)
        ftp.retrbinary('RETR %s' % path, tempfile.write)
        ftp.quit()

        tempfile.seek(0)

        # TODO spostare e rendere genirico
        if path.endswith('.zip'):
            from zipfile import ZipFile
            with ZipFile(tempfile, 'r') as zf:
                with zf.open(path[:-4]) as f:
                    source = f.read()
        else:  # END-TODO
            source = tempfile.read()

        tempfile.close()

        return self.encode(source)


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
