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

import sys, traceback
from terane.toolbox.relay.server import Server
from terane.settings import Settings, ConfigureError

def relay_main():
    settings = Settings(
        usage="[OPTIONS...]",
        description="Logging event relay",
        section="relay")
    try:
        settings.addOption('n', "nprocs",
            override="num processes", help="create NUM child processes", metavar="NUM"
            )
        settings.addLongOption("log-config",
            override="log config file", help="use logging configuration file FILE", metavar="FILE"
            )
        settings.addSwitch("d", "debug",
            override="debug", help="Print debugging information"
            )
        # load configuration
        ns = settings.parse()
        # create the Server and run it
        server = Server()
        server.configure(ns)
        return server.run()
    except ConfigureError, e:
        print >> sys.stderr, "%s: %s" % (settings.appname, e)
    except Exception, e:
        print >> sys.stderr, "\nUnhandled Exception:\n%s\n---\n%s" % (e,traceback.format_exc())
    except KeyboardInterrupt:
        pass
    sys.exit(1)
