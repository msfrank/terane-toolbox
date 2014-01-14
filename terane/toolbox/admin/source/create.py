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

from twisted.internet import reactor
from terane.toolbox.admin.command import AdminCommand
from terane.api.context import ApiContext
from terane.api.source import CreateSourceRequest
from terane.loggers import getLogger

logger = getLogger('terane.toolbox.admin.source.create')

class CreateSourceCommand(AdminCommand):
    """
    """
    def printResult(self, result):
        reactor.stop()

    def printError(self, failure):
        try:
            import StringIO
            s = StringIO.StringIO()
            failure.printTraceback(s)
            logger.debug("caught exception: %s" % s.getvalue())
            raise failure.value
        except ValueError, e:
            print "Operation failed: remote server returned HTTP status %s: %s" % e.args
        except BaseException, e:
            print "Operation failed: %s" % str(e)
        reactor.stop()

    def run(self):
        context = ApiContext(self.host)
        request = CreateSourceRequest(self.source)
        deferred = request.execute(context)
        deferred.addCallback(self.printResult)
        deferred.addErrback(self.printError)
        reactor.run()
        return 0

class CreateSyslogUdpSourceCommand(CreateSourceCommand):
    """
    """
    def configure(self, ns):
        section = ns.section("admin:source:create:syslog-udp")
        (name,) = ns.getArgs(str, names=["NAME"], maximum=1)
        self.source = dict()
        self.source['sourceType'] = 'syslog-udp'
        self.source['name'] = name
        interface = section.getString("interface", None)
        if interface is None:
            raise ConfigureError("missing required parameter --interface")
        self.source['interface'] = interface
        port = section.getInt("port", None)
        if port is None:
            raise ConfigureError("missing required parameter --port")
        self.source['port'] = port
        AdminCommand.configure(self, ns)

class CreateSyslogTcpSourceCommand(CreateSourceCommand):
    """
    """
    def configure(self, ns):
        section = ns.section("admin:source:create:syslog-tcp")
        (name,) = ns.getArgs(str, names=["NAME"], maximum=1)
        self.source = dict()
        self.source['sourceType'] = 'syslog-tcp'
        self.source['name'] = name
        interface = section.getString("interface", None)
        if interface is None:
            raise ConfigureError("missing required parameter --interface")
        self.source['interface'] = interface
        port = section.getInt("port", None)
        if port is None:
            raise ConfigureError("missing required parameter --port")
        self.source['port'] = port
        idleTimeout = section.getInt("idle timeout", None)
        if idleTimeout is not None:
            self.source['idleTimeout'] = idleTimeout
        maxConnections = section.getInt("max connections", None)
        if maxConnections is not None:
            self.source['maxConnections'] = maxConnections
        maxMessageSize = section.getInt("max message size", None)
        if maxMessageSize is not None:
            self.source['maxMessageSize'] = maxMessageSize
        # FIXME: add tls configuration
        AdminCommand.configure(self, ns)
