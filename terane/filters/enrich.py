# Copyright 2010-2013 Michael Frank <msfrank@syntaxjockey.com>
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
from terane.event import FieldIdentifier, parsefield
from terane.loggers import getLogger

logger = getLogger("terane.filters.enrich")

class EnrichFilter(IPlugin):

    def __init__(self, fieldname=None, fieldtype=None, value=None, override=False):
        self.fieldname = fieldname
        self.fieldtype = fieldtype
        self.rawvalue = value
        self.override = bool(override)

    def configure(self, section):
        self.fieldname = section.getString("fieldname", self.fieldname)
        self.fieldtype = section.getString("fieldtype", self.fieldtype)
        self.rawvalue = section.getString("value", self.rawvalue)
        self.override = section.getBoolean("override", self.override)

    def __str__(self):
        return "EnrichFilter(fieldname=%s, fieldtype=%s, value=%s, override=%s)" % (
            self.fieldname, self.fieldtype, self.rawvalue, self.override
        )

    def init(self):
        self.field = FieldIdentifier.fromstring(self.fieldname, self.fieldtype)
        self.value = parsefield(self.field, self.rawvalue)

    def filter(self, event):
        if self.field in event and self.override is False:
            return event
        event.set(self.field, self.value)
        return event
