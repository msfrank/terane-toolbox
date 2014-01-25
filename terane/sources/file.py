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

import sys, time, socket
from terane.plugin import IPlugin
from terane.event import Event
from terane.loggers import getLogger

logger = getLogger('terane.sources.file')

class AbstractFileSource(object):
    """
    Abstract base class for file sources, implementing common logic.
    """
    def __init__(self, *args, **kwargs):
        self.hostname = socket.getfqdn()
        self.linemax = 16384

    def configure(self, section):
        # use the specified origin, otherwise default to host fqdn
        self.hostname = section.getString("origin", self.hostname)
        # ignore lines longer than max line length
        self.linemax = section.getInt("max line length", self.linemax)

    def readline(self):
        """
        Subclasses must implement this method.

        :returns: The next line
        :rtype: str
        """
        raise NotImplementedError()

    def _skipnext(self):
        while True:
            line = self.readline()
            if line == '':
                raise StopIteration
            if line[-1] == '\n':
                line = self.readline()
                if line == '':
                    raise StopIteration
                stripped = line.strip()
                if line[-1] == '\n' and len(stripped) > 0:
                    return line

    def _emit(self):
        line = self.readline()
        # no more data is available
        if line == '':
            raise StopIteration
        stripped = line.strip()
        # we read a complete line, return it
        if line[-1] == '\n' and len(stripped) > 0:
            values = {
                Event.MESSAGE: stripped,
                Event.TIMESTAMP: time.time() * 1000.0,
            	Event.ORIGIN: self.hostname,
            }
            return Event(Event.EMPTY_ID, values)
        # else we have encountered a long line, throw away data until the next line
        values = {
            Event.MESSAGE: self._skipnext().strip(),
            Event.TIMESTAMP: time.time() * 1000.0,
            Event.ORIGIN: self.hostname,
        }
        return Event(Event.EMPTY_ID, values)

    def emit(self):
        """
        Process the next line from the file source, or raise
        StopIteration.

        :returns: The next :class:`Event`
        :rtype: :class:`Event`
        :raises: StopIteration
        """
        try:
            return self._emit()
        except KeyboardInterrupt:
            raise StopIteration

class StdinSource(IPlugin, AbstractFileSource):
    """
    Read in lines from stdin.
    """
    def __init__(self, *args, **kwargs):
        AbstractFileSource.__init__(self, *args, **kwargs)
        self.f = sys.stdin

    def __str__(self):
        return "StdinSource(origin=%s, linemax=%d)" % (self.hostname, self.linemax)

    def readline(self):
        if self.linemax == None:
            return self.f.readline()
        return self.f.readline(self.linemax)