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

from terane.plugin import IPlugin
from terane.event import FieldIdentifier
from terane.loggers import getLogger

logger = getLogger('terane.filters.debug')

class DebugFilter(IPlugin):
    """
    Dump received events to stdout.
    """

    def __str__(self):
        return "DebugFilter()"

    def filter(self, event):
        logger.debug("received %s" % str(event))
        return event
