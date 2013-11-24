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

import os, signal
from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
from tornado.ioloop import IOLoop
from tornado.process import task_id
from loggerglue.rfc5424 import SyslogEntry, syslog_msg
from terane.plugin import IPlugin
from terane.settings import ConfigureError
from terane.loggers import getLogger, startLogging, StdoutHandler, DEBUG

logger = getLogger('terane.toolbox.syslog.sink')

class SyslogSink(IPlugin):
    """
    """
    def __init__(self, ioloop=None):
        self.ioloop = ioloop
        self.host = 'localhost'
        self.port = 514

    def configure(self, section):
        pass

    def init(self):
        self.queue = list()
        self.stream = None

    def _reconnect(self):
        pass

    def consume(self, event):
        self.queue.append(event)
