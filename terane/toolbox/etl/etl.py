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

import sys
from terane.sources.file import StdinSource
from terane.sinks.syslog import SyslogSink
from terane.pipeline import Pipeline
from terane.loggers import getLogger, startLogging, StdoutHandler, DEBUG

logger = getLogger('terane.toolbox.etl.etl')

class ETL(object):
    """
    ETL contains all of the logic necessary to perform an extract-transform-load.
    """

    def configure(self, settings):
        # load configuration
        section = settings.section("etl")
        # publish to the specified store
        self.store = section.getString("store", "main")
        # configure pipeline
        source = StdinSource()
        source.configure(section)
        sink = SyslogSink()
        sink.configure(section)
        self.pipeline = Pipeline(source, sink)
        # configure server logging
        logconfigfile = section.getString('log config file', "%s.logconfig" % settings.appname)
        if section.getBoolean("debug", False):
            startLogging(StdoutHandler(), DEBUG, logconfigfile)
        else:
            startLogging(None)

    def run(self):
        logger.info("executing pipeline '%s'" % self.pipeline)
        self.pipeline.run()
        return 0
