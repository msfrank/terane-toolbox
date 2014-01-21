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

import os, sys, signal, traceback
from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
from tornado.ioloop import IOLoop
from tornado.process import task_id
from loggerglue.rfc5424 import SyslogEntry, syslog_msg
from terane.loggers import getLogger, startLogging, StdoutHandler, DEBUG

logger = getLogger('terane.toolbox.relay.server')

class Server(object):
    """
    Receives TCP syslog messages and processes them using the
    specified pipeline.
    """
    def configure(self, ns):
        # load configuration
        section = ns.section("syslog")
        self.nprocs = section.getInt("num processes", None)
        self.port = section.getInt("listen port", 10514)
        # configure server logging
        logconfigfile = section.getString('log config file', "%s.logconfig" % ns.appname)
        getLogger('tornado')
        if section.getBoolean("debug", False):
            startLogging(StdoutHandler(), DEBUG, logconfigfile)
        else:
            startLogging(None)
        self.handler = TCPHandler(max_buffer_size=65535)

    def run(self):
        logger.debug("starting main loop")
        self.handler.bind(self.port, address=None, backlog=128)
        self.handler.start(self.nprocs)
        signal.signal(signal.SIGINT, self.signal_shutdown)
        signal.signal(signal.SIGTERM, self.signal_shutdown)
        IOLoop.current().handle_callback_exception(self.handle_exception)
        taskid = '0' if task_id() == None else task_id()
        logger.debug("starting task %s (pid %d)" % (taskid, os.getpid()))
        IOLoop.instance().start()
        logger.debug("stopping main loop")

    def handle_exception(self):
        logger.error("callback exception:\n%s\n---\n%s" % (sys.exc_info, traceback.format_exc()))

    def signal_shutdown(self, signum, frame):
        logger.debug("caught signal %d" % signum)
        IOLoop.instance().add_callback_from_signal(self.shut_down)

    def shut_down(self):
        taskid = '0' if task_id() == None else task_id()
        logger.debug("stopping task %s" % taskid)
        self.handler.stop()
        IOLoop.current().stop()

class TCPHandler(TCPServer):
    """
    Accepts incoming connections and hands each to a TCPSession.
    """
    def handle_stream(self, stream, address):
        host,port = address
        logger.debug("accepted connection from %s:%d" % (host,port))
        TCPSession(stream, address)

class TCPSession(object):
    """
    Parses a TCP stream into individual frames.
    """
    def __init__(self, stream, address):
        self.stream = stream
        self.address = address
        stream.set_close_callback(self._stream_closed)
        self.read_frame()

    def closed(self):
        return True if self.stream == None or self.stream.closed() else False

    def read_frame(self):
        try:
            self.stream.read_until(' ', self._length_read)
        except StreamClosedError:
            self.cleanup()

    def _length_read(self, data):
        length = int(data.strip())
        logger.debug("expecting %i bytes" % length)
        try:
            self.stream.read_bytes(length, self._message_read)
        except StreamClosedError:
            self.cleanup()

    def _message_read(self, data):
        logger.debug("read %i bytes for message" % len(data))
        r = syslog_msg.parseString(data)
        message = SyslogEntry.parse(r)
        logger.debug("parsed syslog message: %s" % message)
        self.read_frame()

    def _stream_closed(self):
        logger.debug("stream has been closed")

    def cleanup(self):
        logger.debug("cleaning up stream")
        if not self.stream == None and not self.stream.closed():
            self.stream.close()
        self.stream = None
