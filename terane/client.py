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

import json
from zope.interface import implements
from twisted.internet.defer import succeed
from twisted.web.iweb import IBodyProducer

class JsonProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.entity = json.dumps(body)
        self.length = len(self.entity)

    def startProducing(self, consumer):
        consumer.write(self.entity)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass