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

import urlparse
from loggerglue import constants
from loggerglue.emitter import UDPSyslogEmitter, TCPSyslogEmitter
from loggerglue.rfc5424 import SyslogEntry
from terane.plugin import IPlugin
from terane.event import Event
from terane.settings import ConfigureError
from terane.loggers import getLogger

logger = getLogger('terane.sinks.syslog')

class SyslogSink(IPlugin):
    """
    Send received events to a syslog server via TCP or UDP.
    """

    def __init__(self):
        self.factory = TCPSyslogEmitter
        self.address = 'localhost'
        self.port = 514
        self.args = dict(address=(self.address,self.port))
        self.emitter = None

    def __str__(self):
        return "SyslogSink(%s, %s)" % (self.factory.__name__,
          " ".join(["%s=%s" % (k,v) for k,v in self.args.items()]))

    def configure(self, section):
        url = section.getString("host", None)
        if url != None:
            url = urlparse.urlparse(url)
            netloc = url.netloc if url.netloc != '' else url.path
            if netloc == '':
                raise ConfigureError("host '%s' is not a valid value" % netloc)
            self.address,port = netloc.split(':', 1)
            self.port = int(port)
            self.args.update(dict(address=(self.address,self.port)))
            if url.scheme == 'syslog.udp':
                self.factory = UDPSyslogEmitter
            elif url.scheme == 'syslog.tcp' or url.scheme == '':
                self.factory = TCPSyslogEmitter
            elif url.scheme == 'syslog.tcptls':
                self.factory = TCPSyslogEmitter
                self.args.update(dict(cert_reqs=ssl.CERT_NONE))
            else:
                raise ConfigureError("host has unknown transport scheme '%s'" % url.scheme)

    def init(self):
        logger.debug("using %s with params %s" % (self.factory.__name__,
          " ".join(["%s=%s" % (k,v) for k,v in self.args.items()])))
        self.emitter = self.factory(**self.args)

    def fini(self):
        if self.emitter != None:
            self.emitter.close()

    def _stringtoprival(self, facility, severity):
        _facility = getattr(constants, "LOG_" + facility.upper())
        _severity = getattr(constants, "LOG_" + severity.upper())
        return _facility + _severity

    def consume(self, event):
        """
        Convert the incoming event into a syslog message and send it.

        :param event: The :class:`Event` to send
        :type event: :class:`Event`
        """
        source = event.source(None)
        origin = event.origin(None)
        timestamp = event.timestamp(None)
        message = event.message(None)
        facility = event.literal("facility", "daemon")
        severity = event.literal("severity", "info")
        prival = self._stringtoprival(facility, severity)
        appname = event.literal("appname", None)
        procid = event.literal("procid", None)
        msgid = event.literal("msgid", None)
        msg = SyslogEntry(prival=prival,
                          timestamp=timestamp,
                          hostname=origin,
                          app_name=appname,
                          procid=procid,
                          msgid=msgid,
                          msg=message)
        self.emitter.emit(msg)

# IANA registered private enterprise number for terane
PEN = 42785
