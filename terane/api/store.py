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
from urllib import urlencode
from datetime import datetime
from dateutil.tz import tzutc
from pprint import pformat
from twisted.internet.defer import Deferred
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers

from terane.api import ApiError
from terane.loggers import getLogger
from terane import versionstring

logger = getLogger('terane.api.search')

class DescribeStoreRequest(object):
    """
    Describe the store with the specified id.
    """

    headers = Headers({"User-Agent" : ["terane-toolbox/{}".format(versionstring())]})

    def __init__(self, store):
        """
        """
        self.store = store

    def execute(self, context):
        """
        """
        agent = Agent(context.reactor, context.factory, context.connecttimeout, context.bindaddress, context.connectionpool)
        headers = self.headers.copy()
        url = urlparse.urljoin(context.url.geturl(), '/1/stores/' + self.store)
        request = agent.request("GET", url, headers=headers)
        deferred = Deferred()
        request.addCallback(self.getResponse, agent, context, deferred)
        request.addErrback(self.handleError, agent, context, deferred)
        return deferred

    def getResponse(self, response, agent, context, deferred):
        logger.debug("received response %s %s with headers: %s" % (response.code, response.phrase, response.headers))
        if response.code != 200:
            raise Exception("received error response from server")
        response = readBody(response)
        response.addCallback(self.processResult, agent, context, deferred)
        response.addErrback(self.handleError, agent, context, deferred)

    def processResult(self, entity, agent, context, deferred):
        result = json.loads(entity)
        logger.debug("processing json result: %s" % pformat(result))
        # process statistics
        name = result['name']
        created = result['created']
        created = datetime.fromtimestamp(float(created) / 1000.0, tzutc())
        stats = StoreStatistics(self.store, name, created)
        # pass the result to the deferred
        deferred.callback(stats)

    def handleError(self, failure, agent, context, deferred):
        deferred.errback(failure)


class FindStoreRequest(object):
    """
    Find the store with the specified name.
    """

    headers = Headers({"User-Agent" : ["terane-toolbox/{}".format(versionstring())]})

    def __init__(self, name):
        """
        """
        self.name = name

    def execute(self, context):
        """
        """
        agent = Agent(context.reactor, context.factory, context.connecttimeout, context.bindaddress, context.connectionpool)
        headers = self.headers.copy()
        params = urlencode(dict(name=self.name))
        url = urlparse.urljoin(context.url.geturl(), '/1/stores?' + params)
        request = agent.request("GET", url, headers=headers)
        deferred = Deferred()
        request.addCallback(self.getResponse, agent, context, deferred)
        request.addErrback(self.handleError, agent, context, deferred)
        return deferred

    def getResponse(self, response, agent, context, deferred):
        logger.debug("received response %s %s with headers: %s" % (response.code, response.phrase, response.headers))
        if response.code != 303:
            raise Exception("received error response from server")
        response = readBody(response)
        response.addCallback(self.processResult, agent, context, deferred)
        response.addErrback(self.handleError, agent, context, deferred)

    def processResult(self, entity, agent, context, deferred):
        result = json.loads(entity)
        logger.debug("processing json result: %s" % pformat(result))
        # process statistics
        name = result['name']
        store = result['id']
        created = result['created']
        created = datetime.fromtimestamp(float(created) / 1000.0, tzutc())
        stats = StoreStatistics(store, name, created)
        # pass the result to the deferred
        deferred.callback(stats)

    def handleError(self, failure, agent, context, deferred):
        deferred.errback(failure)

class EnumerateStoresRequest(object):
    """
    Describe all stores.
    """

    headers = Headers({"User-Agent" : ["terane-toolbox/{}".format(versionstring())]})

    def execute(self, context):
        """
        """
        agent = Agent(context.reactor, context.factory, context.connecttimeout, context.bindaddress, context.connectionpool)
        headers = self.headers.copy()
        url = urlparse.urljoin(context.url.geturl(), '/1/stores')
        request = agent.request("GET", url, headers=headers)
        deferred = Deferred()
        request.addCallback(self.getResponse, agent, context, deferred)
        request.addErrback(self.handleError, agent, context, deferred)
        return deferred

    def getResponse(self, response, agent, context, deferred):
        logger.debug("received response %s %s with headers: %s" % (response.code, response.phrase, response.headers))
        if response.code != 200:
            raise Exception("received error response from server")
        response = readBody(response)
        response.addCallback(self.processResult, agent, context, deferred)
        response.addErrback(self.handleError, agent, context, deferred)

    def processResult(self, entity, agent, context, deferred):
        results = json.loads(entity)
        logger.debug("processing json result: %s" % pformat(results))
        # process statistics
        stores = list()
        for result in results['stores']:
            store = result['store']
            name = result['name']
            created = result['created']
            created = datetime.fromtimestamp(float(created) / 1000.0, tzutc())
            stores.append(StoreStatistics(store, name, created))
        # pass the result to the deferred
        deferred.callback(stores)

    def handleError(self, failure, agent, context, deferred):
        deferred.errback(failure)



class StoreStatistics(object):
    """
    Store metadata.
    """
    def __init__(self, store, name, created):
        self.store = store
        self.name = name
        self.created = created
