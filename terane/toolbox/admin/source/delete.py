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
from terane.api.source import DeleteSourceRequest
from terane.loggers import getLogger

logger = getLogger('terane.toolbox.admin.source.delete')

class DeleteSourceCommand(AdminCommand):
    """
    """
    def configure(self, settings):
        section = settings.section("admin:source:delete")
        (name,) = settings.getArgs(str, names=["NAME"], maximum=1)
        self.name = name
        AdminCommand.configure(self, ns)

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
            print "Search failed: remote server returned HTTP status %s: %s" % e.args
        except BaseException, e:
            print "Search failed: %s" % str(e)
        reactor.stop()

    def run(self):
        context = ApiContext(self.host)
        request = DeleteSourceRequest(self.name)
        deferred = request.execute(context)
        deferred.addCallback(self.printResult)
        deferred.addErrback(self.printError)
        reactor.run()
        return 0
