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

import json, urlparse
from uuid import UUID
from datetime import datetime, timedelta
from dateutil.tz import tzutc
from pprint import pformat
from twisted.internet.defer import Deferred
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers

from terane.event import FieldIdentifier, Event
from terane.api import ApiError
from terane.api.client import JsonProducer
from terane.loggers import getLogger
from terane import versionstring

logger = getLogger('terane.api.search')

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
            "store": self.store,
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
        url = urlparse.urljoin(context.url.geturl(), '/1/queries')
        request = agent.request("POST", url, headers=headers, bodyProducer=JsonProducer(createparams))
        logger.debug("creating query with params: %s" % pformat(createparams))
        deferred = Deferred()
        request.addCallback(self.queryCreated, agent, context, deferred)
        request.addErrback(self.handleError, agent, context, deferred)
        return deferred

    def queryCreated(self, response, agent, context, deferred):
        logger.debug("received response %s %s with headers: %s" % (response.code, response.phrase, response.headers))
        if response.code != 201:
            raise Exception("received error response from server")
        response = readBody(response)
        response.addCallback(self.getQuery, agent, context, deferred)
        response.addErrback(self.handleError, agent, context, deferred)

    def getQuery(self, entity, agent, context, deferred):
        logger.debug("received response body: %s" % str(entity))
        query = json.loads(entity)
        queryid = str(query["id"])
        logger.debug("created query %s" % queryid)
        url = urlparse.urljoin(context.url.geturl(), "/1/queries/%s/events" % queryid)
        request = agent.request("GET", url, headers=self.headers.copy())
        request.addCallback(self.getEvents, agent, context, deferred)
        request.addErrback(self.handleError, agent, context, deferred)

    def getEvents(self, response, agent, context, deferred):
        logger.debug("received response %s %s with headers: %s" % (response.code, response.phrase, response.headers))
        if response.code != 200:
            raise Exception("received error response from server")
        logger.debug("received events")
        response = readBody(response)
        response.addCallback(self.processResult, agent, context, deferred)
        response.addErrback(self.handleError, agent, context, deferred)

    def processResult(self, entity, agent, context, deferred):
        result = json.loads(entity)
        logger.debug("processing json result: %s" % pformat(result))
        # build field lookup table
        fields = dict()
        for key,field in result['fields'].items():
            try:
                fields[key] = FieldIdentifier.fromstring(field[1], field[0])
            except KeyError:
              pass
        logger.debug("built field lookup table: %s" % fields)
        # process events
        events = list()
        for eventid,eventfields in result['events']:
            values = dict()
            for key,value in eventfields.items():
                values[fields[key]] = value
            events.append(Event(eventid, values))
        # process statistics 
        stats = SearchStatistics(result['stats'])
        # pass the result to the deferred
        deferred.callback(SearchResult(events, fields, stats, bool(result['finished'])))
 
    def handleError(self, failure, agent, context, deferred):
        deferred.errback(failure)

class SearchResult(object):

    def __init__(self, events, fields, stats, finished):
        self.events = events
        self.fields = fields
        self.stats = stats
        self.finished = finished

class SearchStatistics(object):

    _utc = tzutc()

    def __init__(self, stats):
        self.queryid = UUID(stats['id'])
        self.created = datetime.fromtimestamp(float(stats['created']) / 1000.0, SearchStatistics._utc)
        self.state = stats['state']
        self.runtime = timedelta(milliseconds=stats['runtime'])
        self.numread = stats['numRead']
        self.numsent = stats['numSent']
