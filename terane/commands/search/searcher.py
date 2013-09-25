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

import os, sys, datetime, dateutil.tz, json
from getpass import getpass
from logging import StreamHandler, DEBUG, Formatter
from pprint import pformat
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers
from twisted.internet import reactor
from terane.client import JsonProducer
from terane.loggers import getLogger, startLogging, StdoutHandler, DEBUG
from terane import versionstring

logger = getLogger('terane.commands.search.searcher')

class Searcher(object):

    headers = Headers({"User-Agent" : ["terane-search/{}".format(versionstring())]})

    def configure(self, settings):
        # load configuration
        section = settings.section("search")
        self.host = section.getString("host", 'localhost:45565')
        self.username = section.getString("username", None)
        self.password = section.getString("password", None)
        if section.getBoolean("prompt password", False):
            self.password = getpass("Password: ")
        self.source = section.getString("source", "main")
        self.sortby = section.getList(str, "sort fields", None)
        self.reverse = section.getBoolean("display reverse", False)
        self.limit = section.getInt("limit", 100)
        self.longfmt = section.getBoolean("long format", False)
        self.tz = section.getString("timezone", None)
        if self.tz != None:
            self.tz = dateutil.tz.gettz(self.tz)
        # get the list of fields to display
        self.fields = section.getList(str, "display fields", None)
        # concatenate the command args into the query string
        self.query = ' '.join(settings.args())
        # configure server logging
        logconfigfile = section.getString('log config file', "%s.logconfig" % settings.appname)
        if section.getBoolean("debug", False):
            startLogging(StdoutHandler(), DEBUG, logconfigfile)
        else:
            startLogging(None)
        self.agent = Agent(reactor)

    def run(self):
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
        deferred = self.agent.request("POST", "http://%s/1/queries" % self.host, headers=headers, bodyProducer=JsonProducer(createparams))
        logger.debug("creating query with params: %s" % pformat(createparams))
        deferred.addCallback(self.queryCreated)
        deferred.addErrback(self.printError)
        reactor.run()
        return 0

    def queryCreated(self, response):
        if response.code != 201:
            raise Exception("received non-OK response from server")
        deferred = readBody(response)
        deferred.addCallback(self.getQuery)
        deferred.addErrback(self.printError)

    def getQuery(self, entity):
        query = json.loads(entity)
        queryid = str(query["id"])
        logger.debug("created query %s" % queryid)
        deferred = self.agent.request("GET", "http://%s/1/queries/%s/events" % (self.host, queryid), headers=self.headers.copy())
        deferred.addCallback(self.getEvents)
        deferred.addErrback(self.printError)

    def getEvents(self, response):
        if response.code != 200:
            raise Exception("received non-OK response from server")
        logger.debug("received events")
        deferred = readBody(response)
        deferred.addCallback(self.printResult)
        deferred.addErrback(self.printError)

    def printResult(self, entity):
        import pdb; pdb.set_trace()
        result = json.loads(entity)
        logger.debug("json result: %s" % pformat(result))
        if len(result) > 0:
            events = result['events']
            for eventid,fields in events:
                ts = fields["timestamp"]["DATETIME"]
                del fields["timestamp"]["DATETIME"]
                ts = datetime.datetime.fromtimestamp(ts / 1000, dateutil.tz.tzutc())
                if self.tz:
                    ts = ts.astimezone(self.tz)
                message = fields["message"]["TEXT"]
                del fields["message"]["TEXT"]
                print "%s: %s" % (ts.strftime("%d %b %Y %H:%M:%S %Z"), message)
                if self.longfmt:
                    for fieldname,value in sorted(fields.items(), key=lambda x: x[0]):
                        if self.fields and fieldname not in self.fields:
                            continue
                        print "\t%s=%s" % (fieldname,value)
            print ""
            print "found %i matches in %f seconds." % (len(events), 0.0)
        else:
            print "no matches found."
        reactor.stop()
 
    def printError(self, failure):
        try:
            import StringIO
            s = StringIO.StringIO()
            failure.printTraceback(s)
            logger.debug("caught exception: %s" % s.getvalue())
            raise failure.value
        except ValueError, e:
            print "Search failed: remote server returned HTTP status %s: %s" % e.args
        except BaseException, e:
            print "Search failed: %s" % str(e)
        reactor.stop()
