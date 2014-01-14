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
from datetime import datetime
from dateutil.tz import tzutc
from pprint import pformat
from twisted.internet.defer import Deferred
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers

from terane.api.client import JsonProducer
from terane.loggers import getLogger
from terane import versionstring

logger = getLogger('terane.api.source')

class CreateSourceRequest(object):
    """
    Create a new source with the specified name.
    """

    headers = Headers({
        "Content-Type" : ["application/json"],
        "User-Agent" : ["terane-toolbox/" + versionstring()],
        })

    def __init__(self, settings):
        self.settings = settings

    def execute(self, context):
        """
        """
        agent = Agent(context.reactor, context.factory, context.connecttimeout, context.bindaddress, context.connectionpool)
        headers = self.headers.copy()
        url = urlparse.urljoin(context.url.geturl(), '/1/sources')
        request = agent.request("POST", url, headers=headers, bodyProducer=JsonProducer(self.settings))
        deferred = Deferred()
        request.addCallback(self.getResponse, agent, context, deferred)
        request.addErrback(self.handleError, agent, context, deferred)
        return deferred

    def getResponse(self, response, agent, context, deferred):
        logger.debug("received response %s %s with headers: %s" % (response.code, response.phrase, response.headers))
        if response.code != 201:
            raise Exception("received error response from server")
        response = readBody(response)
        response.addCallback(self.processResult, agent, context, deferred)
        response.addErrback(self.handleError, agent, context, deferred)

    def processResult(self, entity, agent, context, deferred):
        result = json.loads(entity)
        logger.debug("processing json result: %s" % pformat(result))
        # FIXME: return Source
        deferred.callback(None)

    def handleError(self, failure, agent, context, deferred):
        deferred.errback(failure)


class DeleteSourceRequest(object):
    """
    Delete the source with the specified name.
    """

    headers = Headers({"User-Agent" : ["terane-toolbox/" + versionstring()]})

    def __init__(self, name):
        self.name = name


class DescribeSourceRequest(object):
    """
    Describe the source with the specified name.
    """

    headers = Headers({"User-Agent" : ["terane-toolbox/" + versionstring()]})

    def __init__(self, name):
        """
        """
        self.name = name

    def execute(self, context):
        """
        """
        agent = Agent(context.reactor, context.factory, context.connecttimeout, context.bindaddress, context.connectionpool)
        headers = self.headers.copy()
        url = urlparse.urljoin(context.url.geturl(), '/1/sources/' + self.name)
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
        source = result['settings']
        # pass the result to the deferred
        deferred.callback(source)

    def handleError(self, failure, agent, context, deferred):
        deferred.errback(failure)


class EnumerateSourcesRequest(object):
    """
    Describe all sources.
    """

    headers = Headers({"User-Agent" : ["terane-toolbox/" + versionstring()]})

    def execute(self, context):
        """
        """
        agent = Agent(context.reactor, context.factory, context.connecttimeout, context.bindaddress, context.connectionpool)
        headers = self.headers.copy()
        url = urlparse.urljoin(context.url.geturl(), '/1/sources')
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
        sources = list()
        for result in results:
            settings = result['settings']
            sources.append(settings)
        # pass the result to the deferred
        deferred.callback(sources)

    def handleError(self, failure, agent, context, deferred):
        deferred.errback(failure)
