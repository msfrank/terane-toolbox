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
    """
    Encapsulates a node specification, which consists of a name and a
    map of key-value parameters.
    """
    def __init__(self, name, params):
        self.name = name
        self.params = params

class DropEvent(Exception):
    """
    If any node in a :class:`Pipeline` raises this exception, the currently
    processed event is dropped and the pipeline continues with the next event
    from the source.
    """

class Pipeline(object):
    """
    A pipeline consists of a source, a sink, and a sequence of zero or more
    filters.  A pipeline may be executed by executing the run() method, which 
    synchronously pulls events from the source, feeds them through each filter,
    and pushes them into the sink until there are no more events left (the
    source raises StopIteration).
    """

    def __init__(self, source, sink, *filters):
        self._source = source
        self._sink = sink
        self._filters = filters

    def __str__(self):
        source = str(self._source)
        sink = str(self._sink)
        if len(self._filters) > 0:
            filters = " ~> ".join([str(f) for f in self._filters])
            return "%s ~> %s ~> %s" % (source, filters, sink)
        return "%s ~> %s" % (source, sink)

    def run(self):
        """
        Run the pipeline synchronously until there are no more events.

        :raises: Exception
        """
        self._source.init()
        self._sink.init()
        for f in self._filters:
            f.init()
        try:
            while True:
                self._sink.consume(self._next())
        except StopIteration:
            pass
        finally:
            self._source.fini()
            self._sink.fini()
            for f in self._filters:
                f.fini()

    def _next(self):
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
                _event = self._source.emit()
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


