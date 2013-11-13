# Copyright 2010,2011 Michael Frank <msfrank@syntaxjockey.com>
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

from pyparsing import *
from terane.settings import PipelineSettings

keyvalue = Word(alphas, alphanums) + Suppress("=") + quotedString
def _parseKeyvalue(tokens):
    return (tokens[0], tokens[1])
keyvalue.setParseAction(_parseKeyvalue)

node = Word(alphas, alphanums) + ZeroOrMore(keyvalue)
def _parseNode(tokens):
    name = tokens[0]
    params = dict(tokens[1:])
    return NodeSpec(name, params)
node.setParseAction(_parseNode)

nodeseq = node + ZeroOrMore("|" + node)

class NodeSpec(object):
    def __init__(self, name, params):
        self.name = name
        self.params = params

class DropEvent(Exception):
    pass

class Pipeline(object):
    """
    """
    def __init__(self, source, *filters):
        self._source = source
        self._filters = filters

    def next(self):
        """
        Return the next :class:`Event` from the pipeline, or raise
        StopIteration.

        :returns: The next :class:`Event`
        :rtype: :class:`Event`
        :raises: StopIteration
        """
        event = None
        while event == None:
            try:
                _event = self._source.next()
                for f in self._filters:
                    _event = f.filter(_event)
                event = _event
            except DropEvent:
                pass
        return event

def makepipeline(spec):
    """
    Construct a :class:`Pipeline` from the supplied string spec.

    :param spec: The pipeline specification
    :type spec: str
    :returns: A new :class:`Pipeline`
    :rtype: :class:`Pipeline`
    """
    nodes = nodeseq.parseString(spec, parseAll=True)
    settings = PipelineSettings(nodes)
    return settings


