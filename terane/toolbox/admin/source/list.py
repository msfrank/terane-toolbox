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
from terane.api.source import EnumerateSourcesRequest
from terane.loggers import getLogger

logger = getLogger('terane.toolbox.admin.source.list')

class ListSourcesCommand(AdminCommand):
    """
    """
    def configure(self, ns):
        AdminCommand.configure(self, ns)

    def printResult(self, sources):
        for source in sources:
            name = source['name']
            del source['name']
            print "  name: " + name
            sourceType = source['sourceType']
            del source['sourceType']
            print "  type: " + sourceType
            for key,value in sorted(source.items()):
                print "    %s: %s" % (key,value)
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
        request = EnumerateSourcesRequest()
        deferred = request.execute(context)
        deferred.addCallback(self.printResult)
        deferred.addErrback(self.printError)
        reactor.run()
        return 0
