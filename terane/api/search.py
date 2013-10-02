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

import os, sys, datetime, dateutil.tz, json
from logging import StreamHandler, DEBUG, Formatter
from pprint import pformat
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers

from terane.api import Field, Event, ApiError
from terane.client import JsonProducer
from terane.loggers import getLogger, startLogging, StdoutHandler, DEBUG
from terane import versionstring

logger = getLogger('terane.commands.api.search')

class SearchRequest(object):
    """
    """

    headers = Headers({"User-Agent" : ["terane-toolbox/{}".format(versionstring())]})

    def __init__(self, query, store, fields=None, sortby=None, limit=None, reverse=False):
        """
        """
        self.query = query
        self.store = store
        self.fields = fields
        self.sortby = sortby
        self.limit = limit
        self.reverse = reverse

    def execute(self, context):
        """
        """
        agent = Agent(context.reactor, context.factory, context.connecttimeout, context.bindaddress, context.connectionpool)
        createparams = {
            "query": self.query,
            "store": self.source,
        }
        if self.fields != None:
            createparams['fields'] = self.fields
        if self.sortby != None:
            createparams['sortBy'] = self.sortby
        if self.limit != None:
            createparams['limit'] = self.limit
        if self.reverse == True:
            createparams['reverse'] = self.reverse
        headers = self.headers.copy()
        headers.addRawHeader("Content-Type", "application/json"),
        request = agent.request("POST", "http://%s/1/queries" % self.host, headers=headers, bodyProducer=JsonProducer(createparams))
        logger.debug("creating query with params: %s" % pformat(createparams))
        deferred = Deferred()
        request.addCallback(self.queryCreated, agent, deferred)
        request.addErrback(self.handleError, agent, deferred)
        return deferred

    def queryCreated(self, response, agent, deferred):
        if response.code != 201:
            raise Exception("received non-OK response from server")
        deferred = readBody(response)
        deferred.addCallback(self.getQuery, agent, deferred)
        deferred.addErrback(self.handleError, agent, deferred)

    def getQuery(self, entity, agent, deferred):
        query = json.loads(entity)
        queryid = str(query["id"])
        logger.debug("created query %s" % queryid)
        deferred = self.agent.request("GET", "http://%s/1/queries/%s/events" % (self.host, queryid), headers=self.headers.copy())
        deferred.addCallback(self.getEvents, agent, deferred)
        deferred.addErrback(self.handleError, agent, deferred)

    def getEvents(self, response, agent, deferred):
        if response.code != 200:
            raise Exception("received non-OK response from server")
        logger.debug("received events")
        deferred = readBody(response)
        deferred.addCallback(self.processResult, agent, deferred)
        deferred.addErrback(self.handleError, agent, deferred)

    def processResult(self, entity, agent, deferred):
        result = json.loads(entity)
        logger.debug("processing json result: %s" % pformat(result))
        # build field lookup table
        fields = dict()
        for key,field in result['fields'].items():
            try:
                fields[key] = Field.fromstring(field['name'], field['type'])
            except KeyError:
              pass
        logger.debug("built field lookup table: %s" % fields)
        # process events
        events = list()
        for eventid,eventfields in events:
            values = dict()
            for key,value in eventfields:
                field = fields[key]
                values[Field.fromstring(fieldname, fieldtype)] = value
            events.append(Event(eventid, values))
        # process statistics 
        stats = None
        # pass the result to the deferred
        deferred.callback(SearchResult(events, fields, stats, bool(result['finished'])))
 
    def handleError(self, failure, agent, deferred):
        deferred.errback(failure)

class SearchResult(object):

    def __init__(self, events, fields, stats, finished):
        self.events = events
        self.fields = fields
        self.stats = stats
        self.finished = finished
