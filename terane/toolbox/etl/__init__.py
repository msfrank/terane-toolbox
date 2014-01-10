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
from terane.toolbox.etl.etl import ETL
from terane.settings import Settings, ConfigureError

def etl_main():
    settings = Settings(
        usage="[OPTIONS...] PIPELINE [ - | FILE...]",
        description="Process the specified ETL pipeline",
        section="etl")
    try:
        settings.addOption("H", "host",
            override="host", help="connect to syslog server HOST", metavar="HOST"
            )
        settings.addOption("f", "filters",
            override="filters", help="use filter pipeline SPEC", metavar="SPEC"
            )
        settings.addOption("s", "sink",
            override="sink", help="publish events to the specified STORE", metavar="STORE"
            )
        settings.addLongOption("log-config",
            override="log config file", help="use logging configuration file FILE", metavar="FILE"
            )
        settings.addSwitch("d", "debug",
            override="debug", help="Print debugging information"
            )
        # load configuration
        settings.load()
        # create the ETL and run it
        etl = ETL()
        etl.configure(settings)
        return etl.run()
    except ConfigureError, e:
        print >> sys.stderr, "%s: %s" % (settings.appname, e)
    except Exception, e:
        print >> sys.stderr, "\nUnhandled Exception:\n%s\n---\n%s" % (e,traceback.format_exc())
    sys.exit(1)
