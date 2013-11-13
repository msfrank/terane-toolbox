# Copyright 2010,2011 Michael Frank <msfrank@syntaxjockey.com>
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

import sys, urlparse
from loggerglue.emitter import TCPSyslogEmitter, UDPSyslogEmitter
from terane.api import Event, FieldIdentifier
from terane.pipeline import Pipeline
from terane.settings import ConfigureError
from terane.loggers import getLogger, startLogging, StdoutHandler, DEBUG

logger = getLogger('terane.commands.etl.etl')

class ETL(object):
    """
    ETL contains all of the logic necessary to perform an extract-transform-load.
    """

    def configure(self, settings):
        # load configuration
        section = settings.section("etl")
        # determine syslog emitter
        url = urlparse.urlparse(section.getString("host", 'syslog.tcp://localhost:514'))
        netloc = url.netloc if url.netloc != '' else url.path
        if netloc == '':
            raise ConfigureError("host '%s' is not a valid value" % netloc)
        host,port = netloc.split(':', 1)
        port = int(port)
        args = dict(address=(host,port))
        if url.scheme == 'syslog.udp':
            factory = UDPSyslogEmitter
        elif url.scheme == 'syslog.tcp':
            factory = TCPSyslogEmitter
            args = dict(address=(host,port))
        elif url.scheme == 'syslog.tcptls':
            factory = TCPSyslogEmitter
            args = dict(address=(host,port))
        elif url.scheme == '':
            factory = TCPSyslogEmitter
        else:
            raise ConfigureError("host has unknown transport scheme '%s'" % url.scheme)
        # publish to the specified store
        self.store = section.getString("store", "main")
        # ignore lines longer than max line length
        linemax = section.getInt("max line length", 16384)
        source = FileSource(sys.stdin, linemax)
        self.pipeline = Pipeline(source)
        # configure server logging
        logconfigfile = section.getString('log config file', "%s.logconfig" % settings.appname)
        if section.getBoolean("debug", False):
            startLogging(StdoutHandler(), DEBUG, logconfigfile)
        else:
            startLogging(None)

    def run(self):
        try:
            while True:
                event = self.pipeline.next()
                print event
        except StopIteration:
            pass
        return 0

class FileSource(object):
    """
    """

    linefield = FieldIdentifier("line", FieldIdentifier.TEXT)

    def __init__(self, f, linemax=None):
        self.f = f
        self.linemax = linemax

    def _readline(self):
        if self.linemax == None:
            return self.f.readline()
        return self.f.readline(self.linemax)

    def _skipnext(self):
        while True:
            line = self._readline()
            if line == '':
                raise StopIteration
            if line[-1] == '\n':
                line = self._readline()
                if line == '':
                    raise StopIteration
                if line[-1] == '\n':
                    return line

    def next(self):
        """
        Process the next line from the file source, or raise
        StopIteration.

        :returns: The next :class:`Event`
        :rtype: :class:`Event`
        :raises: StopIteration
        """
        line = self._readline()
        # no more data is available
        if line == '':
            raise StopIteration
        # we read a complete line, return it
        if line[-1] == '\n':
            values = {FileSource.linefield: line.rstrip()}
            return Event(Event.EMPTY_ID, values)
        # else we have encountered a long line, throw away data until the next line
        values = {FileSource.linefield: self._skipnext().rstrip()}
        return Event(Event.EMPTY_ID, values)
