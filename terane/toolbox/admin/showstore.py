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
from terane.api.store import DescribeStoreRequest, FindStoreRequest
from terane.settings import Settings, ConfigureError
from terane.loggers import getLogger, startLogging, StdoutHandler, DEBUG

logger = getLogger('terane.toolbox.admin.showstore')

class Operation(object):
    """
    """

    def configure(self, settings):
        # load configuration
        section = settings.section("show-store")
        self.host = urlparse.urlparse(section.getString("host", 'http://localhost:8080'))
        self.username = section.getString("username", None)
        self.password = section.getString("password", None)
        self.reverse = section.getBoolean("reverse query", False)
        if section.getBoolean("prompt password", False):
            self.password = getpass("Password: ")
        (self.key,) = settings.args()
        # configure logging
        logconfigfile = section.getString('log config file', "%s.logconfig" % settings.appname)
        if section.getBoolean("debug", False):
            startLogging(StdoutHandler(), DEBUG, logconfigfile)
        else:
            startLogging(None)

    def printResult(self, stats):
        if self.reverse:
            print '"' + stats.store + '"'
            print "  name: " + stats.name
            print "  created: " + stats.created.isoformat()
        else:
            print '"' + stats.name + '"'
            print "  id: " + stats.store
            print "  created: " + stats.created.isoformat()
        reactor.stop()

    def printError(self, failure):
        try:
            import StringIO
            s = StringIO.StringIO()
            failure.printTraceback(s)
            logger.debug("caught exception: %s" % s.getvalue())
            raise failure.value
        except ValueError, e:
            print "Search failed: remote server returned HTTP status %s: %s" % e.args
        except BaseException, e:
            print "Search failed: %s" % str(e)
        reactor.stop()

    def run(self):
        context = ApiContext(self.host)
        request = FindStoreRequest(self.key) if not self.reverse else DescribeStoreRequest(self.key)
        deferred = request.execute(context)
        deferred.addCallback(self.printResult)
        deferred.addErrback(self.printError)
        reactor.run()
        return 0

def show_store_main():
    try:
        settings = Settings(usage="[OPTIONS...] STORE")
        settings.addOption("H", "host", "show-store", "host",
            help="Connect to terane server HOST", metavar="HOST"
            )
        settings.addOption("u", "username", "show-store", "username",
            help="Authenticate with username USER", metavar="USER"
            )
        settings.addOption("p", "password", "show-store", "password",
            help="Authenticate with password PASS", metavar="PASS"
            )
        settings.addSwitch("P", "prompt-password", "show-store", "prompt password",
            help="Prompt for a password"
            )
        settings.addSwitch("r", "reverse", "show-store", "reverse query",
                           help="STORE is an id, instead of a name"
        )
        settings.addOption('', "log-config", "show-store", "log config file",
            help="use logging configuration file FILE", metavar="FILE"
            )
        settings.addSwitch("d", "debug", "show-store", "debug",
            help="Print debugging information"
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
