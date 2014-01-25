# Copyright 2013 Michael Frank <msfrank@syntaxjockey.com>
#
# This file is part of Terane.
#
# Terane is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Terane is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Terane.  If not, see <http://www.gnu.org/licenses/>.

import os, socket, time, errno
from terane.plugin import IPlugin
from terane.sources.file import AbstractFileSource
from terane.event import Event
from terane.loggers import getLogger

logger = getLogger('terane.sources.tail')

class TailSource(IPlugin, AbstractFileSource):
    """
    Read in lines from the specified file by tailing.
    """
    def __init__(self, *args, **kwargs):
        AbstractFileSource.__init__(self, *args, **kwargs)
        self.path = None
        self.sleeptime = 5

    def __str__(self):
        return "TailSource(path=%s, origin=%s, linemax=%d)" % (self.path, self.hostname, self.linemax)

    def configure(self, section):
        AbstractFileSource.configure(self, section)
        self.path = section.getPath("path", self.path)

    def init(self):
        self.f = None
        self.prevstats = None
        self.position = 0
        self.buffer = ""
        self.errno = None
        self.skipcount = 0

    def _wait(self):
        time.sleep(self.sleeptime)

    def readline(self):
        """
        Loop forever adding bytes read to the buffer until we encounter
        one of two exit conditions:

          1) we encounter a newline
          2) we fill the buffer without encountering a newline

        In either case, we return the contents of the buffer and rely on
        the AbstractFileSource implementation of emit() to ignore messages
        which are too long.
        """
        while True:
            # get current file statistics
            try:
                currstats = os.stat(self.path)
            except (IOError,OSError), (_errno, errstr):
                if _errno != errno.ENOENT and _errno != self.errno:
                    logger.warning("failed to stat() %s: %s" % (self.path, errstr))
                    self.errno = errno
                continue
            if self.errno is not None:
                self.errno = None
            prevstats = self.prevstats
            self.prevstats = currstats

            # open the file if needed
            if self.f is None:
                self.f = open(self.path, 'r')
                logger.debug("opened %s" % self.path)
                self.skipcount = 0
                # if this is the first file open, then start reading from
                # the end of the file
                if prevstats is None:
                    self.position = currstats.st_size
                # otherwise start reading from the beginning of the file
                else:
                    self.position = 0
            f = self.f

            # check for file metadata changes
            if prevstats is not None:
                # the file inode and/or underlying block device changed
                if prevstats.st_dev != currstats.st_dev or prevstats.st_ino != currstats.st_ino:
                    logger.debug("detected VFS change to %s" % self.path)
                    self.f = None
                # the file shrank
                elif self.position > currstats.st_size:
                    delta = self.position - currstats.st_size
                    logger.info("file %s shrank by %i bytes" % (self.path, delta))
                    # reset the buffer
                    self.buffer = ""
                    # reset position to the new end of the file
                    self.position = currstats.st_size

            # delta is the number of unread bytes we know about
            delta = currstats.st_size - self.position
            # if the file hasn't changed, then wait for activity
            if delta == 0:
                self._wait()
                continue
            logger.debug("position=%i, st_size=%i" % (self.position, currstats.st_size))

            # read up to readsize bytes into buffer
            readsize = min(self.linemax - len(self.buffer), currstats.st_size - self.position)
            f.seek(self.position)
            data = f.readline(readsize)
            logger.debug("read %i bytes" % len(data))
            self.buffer = self.buffer + data
            self.position = f.tell()

            # return the buffer, which may or may not be complete
            if self.buffer.endswith('\n') or len(self.buffer) == self.linemax:
                buffer = self.buffer
                self.buffer = ""
                return buffer
