# Copyright 2010-2013 Michael Frank <msfrank@syntaxjockey.com>
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

import re, dateutil.parser
from terane.plugin import IPlugin
from terane.event import Event
from terane.sinks.syslog import SyslogSink
from terane.pipeline import DropEvent
from terane.loggers import getLogger

logger = getLogger("terane.filters.syslog_format")

class SyslogFormatFilter(IPlugin):

    _linematcher = re.compile(r'(?P<ts>[A-Za-z]{3} [ \d]\d \d\d:\d\d\:\d\d) (?P<hostname>\S*) (?P<msg>.*)')
    _tagmatcher = re.compile(r'^(\S+)\[(\d+)\]:$|^(\S+):$')

    def __str__(self):
        return "SyslogFormatFilter()"

    def filter(self, event):
        # split the line into timestamp, hostname, and message
        line = event.message()
        m = SyslogFormatFilter._linematcher.match(line)
        if m == None:
            raise DropEvent("line is not in syslog format")
        ts,hostname,msg = m.group('ts','hostname','msg')
        if ts == None or hostname == None or msg == None:
            raise DropEvent("line is not in syslog format")
        # parse the timestamp
        try:
            event.set(Event.TIMESTAMP, dateutil.parser.parse(ts))
        except Exception, e:
            raise DropEvent("failed to parse ts '%s': %s" % (ts, e))
        event.set(Event.ORIGIN, hostname)
        # split the message into tag and content
        tag,content = msg.split(' ', 1)
        m = SyslogFormatFilter._tagmatcher.match(tag)
        if m == None:
            raise DropEvent("line has an invalid tag")
        data = m.groups()
        if data[0] != None and data[1] != None:
            event.set(SyslogSink.APPNAME, data[0])
            event.set(SyslogSink.PROCID, data[1])
        elif data[2] != None:
            event.set(SyslogSink.APPNAME, data[2])
        else:
            raise DropEvent("line has an invalid tag")
        event.set(Event.MESSAGE, content)
        return event
