# Copyright 2010-2014 Michael Frank <msfrank@syntaxjockey.com>
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

import urlparse, getpass
from terane.loggers import startLogging, StdoutHandler, DEBUG

class Command(object):
    def __call__(self, ns):
        self.configure(ns)
        return self
    def configure(self, ns):
        pass
    def run(self):
        return 0

class AdminCommand(Command):
    """
    """
    def configure(self, ns):
        section = ns.section("admin")
        self.host = urlparse.urlparse(section.getString("host", 'http://localhost:8080'))
        self.username = section.getString("username", None)
        self.password = section.getString("password", None)
        if section.getBoolean("prompt password", False):
            self.password = getpass.getpass("Password: ")
        logconfigfile = section.getString('log config file', "%s.logconfig" % ns.appname)
        if section.getBoolean("debug", False):
            startLogging(StdoutHandler(), DEBUG, logconfigfile)
        else:
            startLogging(None)

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

