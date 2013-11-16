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
from terane.plugin import PluginManager
from terane.pipeline import Pipeline, parsepipeline, makepipeline
from terane.settings import ConfigureError
from terane.loggers import getLogger, startLogging, StdoutHandler, DEBUG

logger = getLogger('terane.toolbox.run.runner')

class Runner(object):
    """
    Execute a pipeline.
    """

    def configure(self, settings):
        # load configuration
        section = settings.section("run")
        # configure pipeline
        plugins = PluginManager()
        args = settings.args()
        if len(args) > 0:
            spec = " ".join(args)
        else:
            spec = section.getString("pipeline", None)
        if spec == None:
            raise ConfigureError("no pipeline was specified")
        nodes = makepipeline(parsepipeline(spec))
        if len(nodes) < 2:
            raise ConfigureError("pipeline must consist of at least one source and one sink")
        source = nodes.pop(0)
        sink = nodes.pop(-1)
        filters = nodes
        self.pipeline = Pipeline(source, sink, filters)
        # configure server logging
        logconfigfile = section.getString('log config file', "%s.logconfig" % settings.appname)
        if section.getBoolean("debug", False):
            startLogging(StdoutHandler(), DEBUG, logconfigfile)
        else:
            startLogging(None)

    def run(self):
        logger.info("executing pipeline '%s'" % self.pipeline)
        self.pipeline.run()
        logger.info("processed %i events, dropped %i" % (self.pipeline.processed, self.pipeline.dropped))
        return 0
