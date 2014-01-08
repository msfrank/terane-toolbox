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

import sys, traceback, urlparse
from getpass import getpass
from twisted.internet import reactor
from terane.api.context import ApiContext
from terane.api.sink import CreateSinkRequest
from terane.settings import Settings, ConfigureError
from terane.loggers import getLogger, startLogging, StdoutHandler, DEBUG

logger = getLogger('terane.toolbox.admin.sink.create')

class Operation(object):
    """
    """

    def configure(self, settings):
        # load configuration
        section = settings.section("create-sink")
        self.host = urlparse.urlparse(section.getString("host", 'http://localhost:8080'))
        self.username = section.getString("username", None)
        self.password = section.getString("password", None)
        if section.getBoolean("prompt password", False):
            self.password = getpass("Password: ")
        sinktype = settings.getStack()[0]
        if sinktype == 'cassandra':
            section = settings.section("create-sink:cassandra")
            (name,) = settings.getArgs(str, names=["NAME"], maximum=1)
            self.sink = dict()
            self.sink['name'] = name
            self.sink['sinkType'] = 'cassandra'
            self.sink['flushInterval'] = section.getInt("flush interval", 60000)
        else:
            raise ConfigureError("invalid sink type '%s'" % sinktype)
        # configure logging
        logconfigfile = section.getString('log config file', "%s.logconfig" % settings.appname)
        if section.getBoolean("debug", False):
            startLogging(StdoutHandler(), DEBUG, logconfigfile)
        else:
            startLogging(None)

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
        request = CreateSinkRequest(self.settings)
        deferred = request.execute(context)
        deferred.addCallback(self.printResult)
        deferred.addErrback(self.printError)
        reactor.run()
        return 0

def create_sink_main():
    try:
        # global options
        settings = Settings(
            usage="[OPTIONS...] SINKTYPE [SINKOPTIONS...] NAME",
            subusage="Available sink types:"
            )
        settings.addOption("H", "host", "create-sink", "host",
            help="Connect to terane server HOST", metavar="HOST"
            )
        settings.addOption("u", "username", "create-sink", "username",
            help="Authenticate with username USER", metavar="USER"
            )
        settings.addOption("p", "password", "create-sink", "password",
            help="Authenticate with password PASS", metavar="PASS"
            )
        settings.addSwitch("P", "prompt-password", "create-sink", "prompt password",
            help="Prompt for a password"
            )
        settings.addOption('', "log-config", "create-sink", "log config file",
            help="use logging configuration file FILE", metavar="FILE"
            )
        settings.addSwitch("d", "debug", "create-sink", "debug",
            help="Print debugging information"
            )
        # cassandra specific options
        cassandra = settings.addSubcommand("cassandra",
            usage="[SINKOPTIONS...] NAME",
            description="Create a new Cassandra sink"
            )
        cassandra.addOption('f', "flush-interval", "create-sink:cassandra", "flush interval",
            help="Use flush interval MILLIS", metavar="MILLIS"
            )

        # load configuration
        settings.load()
        # create the Searcher and run it
        operation = Operation()
        operation.configure(settings)
        return operation.run()
    except ConfigureError, e:
        print >> sys.stderr, "%s: %s" % (settings.appname, e)
    except Exception, e:
        print >> sys.stderr, "\nUnhandled Exception:\n%s\n---\n%s" % (e,traceback.format_exc())
    sys.exit(1)
