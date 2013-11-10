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

from collections import Mapping
from datetime import datetime
from dateutil.tz import tzutc

class FieldIdentifier(object):
    """
    """

    TEXT      = 1
    LITERAL   = 2
    INTEGER   = 3
    FLOAT     = 4
    DATETIME  = 5
    ADDRESS   = 6
    HOSTNAME  = 7

    _idlookup = {
        'TEXT': TEXT,
        'LITERAL': LITERAL,
        'INTEGER': INTEGER,
        'FLOAT': FLOAT,
        'DATETIME': DATETIME,
        'ADDRESS': ADDRESS,
        'HOSTNAME': HOSTNAME
    }
    _namelookup = {
        TEXT: 'TEXT',
        LITERAL: 'LITERAL',
        INTEGER: 'INTEGER',
        FLOAT: 'FLOAT',
        DATETIME: 'DATETIME',
        ADDRESS: 'ADDRESS',
        HOSTNAME: 'HOSTNAME'
    }

    def __init__(self, fieldname, fieldtype):
        self.name = unicode(fieldname)
        self.type = fieldtype

    def __eq__(self, other):
        return self.name == other.name and self.type == other.type

    def __str__(self):
        return str("%s:%s" % (FieldIdentifier._namelookup[self.type], self.name))

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash("%d:%s" % (self.type,self.name))

    @classmethod
    def fromstring(cls, fieldname, fieldtype):
        return FieldIdentifier(fieldname, FieldIdentifier._idlookup[fieldtype.upper()])

class Event(Mapping):
    """
    """

    _utc = tzutc()

    _parsefield = {
        FieldIdentifier.TEXT: (lambda x: unicode(x)),
        FieldIdentifier.LITERAL: (lambda x: unicode(x)),
        FieldIdentifier.INTEGER: (lambda x: int(x)),
        FieldIdentifier.FLOAT: (lambda x: float(x)),
        FieldIdentifier.DATETIME: (lambda x: datetime.fromtimestamp(float(x) / 1000.0, Event._utc)),
        FieldIdentifier.ADDRESS: (lambda x: str(x)),
        FieldIdentifier.HOSTNAME: (lambda x: str(x)),
    }

    _MISSING = "missing"

    def __init__(self, id, values):
        self._id = id
        self._values = dict()
        for field,value in values.items():
            self._values[(field.name,field.type)] = Event._parsefield[field.type](value)

    @property
    def id(self):
        return self._id

    def items(self):
        return self._values.items()

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        return iter(self._values)

    def __contains__(self, key):
        return key in self._values

    def __getitem__(self, key):
        return self._values[key]

    def text(self, key, default=_MISSING):
        try:
            return self._values[(key, FieldIdentifier.TEXT)]
        except KeyError:
            if default is Event._MISSING:
                raise
            return default

    def literal(self, key, default=_MISSING):
        try:
            return self._values[(key, FieldIdentifier.LITERAL)]
        except KeyError:
            if default is Event._MISSING:
                raise
            return default


    def integer(self, key, default=_MISSING):
        try:
            return self._values[(key, FieldIdentifier.INTEGER)]
        except KeyError:
            if default is Event._MISSING:
                raise
            return default

    def float(self, key, default=_MISSING):
        try:
            return self._values[(key, FieldIdentifier.FLOAT)]
        except KeyError:
            if default is Event._MISSING:
                raise
            return default

    def datetime(self, key, default=_MISSING):
        try:
            return self._values[(key, FieldIdentifier.DATETIME)]
        except KeyError:
            if default is Event._MISSING:
                raise
            return default

    def address(self, key, default=_MISSING):
        try:
            return self._values[(key, FieldIdentifier.ADDRESS)]
        except KeyError:
            if default is Event._MISSING:
                raise
            return default

    def hostname(self, key, default=_MISSING):
        try:
            return self._values[(key, FieldIdentifier.HOSTNAME)]
        except KeyError:
            if default is Event._MISSING:
                raise
            return default

    def source(self, default=_MISSING):
        return self.literal('source', default)

    def origin(self, default=_MISSING):
        return self.hostname('origin', default)

    def timestamp(self, default=_MISSING):
        return self.datetime('timestamp', default)

    def message(self, default=_MISSING):
        return self.text('message', default)

    _special = (
        ('source', FieldIdentifier.LITERAL),
        ('origin', FieldIdentifier.HOSTNAME),
        ('timestamp', FieldIdentifier.DATETIME),
        ('message', FieldIdentifier.TEXT)
    )

    def fields(self):
        for fieldid,value in self.items():
            if fieldid not in Event._special:
                yield (FieldIdentifier(fieldid[0], fieldid[1]), value)


class ApiError(Exception):

    def __init__(self, message, code):
        self.code = code
        self.message = message
