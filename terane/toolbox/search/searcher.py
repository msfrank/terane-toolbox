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

import urlparse, dateutil
from getpass import getpass
from twisted.internet import reactor
from terane.event import FieldIdentifier
from terane.api.context import ApiContext
from terane.api.search import SearchRequest
from terane.loggers import getLogger, startLogging, StdoutHandler, DEBUG

logger = getLogger('terane.toolbox.search.searcher')

class Searcher(object):
    """
    """
    def configure(self, ns):
        # load configuration
        section = ns.section("search")
        self.host = urlparse.urlparse(section.getString("host", 'http://localhost:8080'))
        self.username = section.getString("username", None)
        self.password = section.getString("password", None)
        if section.getBoolean("prompt password", False):
            self.password = getpass("Password: ")
        self.store = section.getString("store", "main")
        # get the list of fields to retrieve
        self.fields = section.getList("retrieve fields", str, None)
        if self.fields != None:
            pass
        # get the list of fields to sort by
        self.sortby = section.getList("sort fields", str, None)
        if self.sortby != None:
            pass
        self.reverse = section.getBoolean("sort reverse", False)
        self.limit = section.getInt("limit", 100)
        self.longfmt = section.getBoolean("long format", False)
        self.tz = section.getString("timezone", None)
        if self.tz != None:
            self.tz = dateutil.tz.gettz(self.tz)
        # concatenate the command args into the query string
        self.query = ' '.join(ns.args)
        # configure server logging
        logconfigfile = section.getString('log config file', "%s.logconfig" % ns.appname)
        if section.getBoolean("debug", False):
            startLogging(StdoutHandler(), DEBUG, logconfigfile)
        else:
            startLogging(None)

    def _parseField(self, s):
        try:
            fieldname,fieldtype = s.split(':', 1)
            return FieldIdentifier.fromstring(fieldname, fieldtype)
        except:
            return FieldIdentifier.fromstring(s, '')

    def run(self):
        context = ApiContext(self.host)
        request = SearchRequest(self.query, self.store, self.fields, self.sortby, self.limit, self.reverse)
        deferred = request.execute(context)
        deferred.addCallback(self.printResult)
        deferred.addErrback(self.printError)
        reactor.run()
        return 0

    def printResult(self, result):
        if len(result.events) > 0:
            for event in result.events:
                # get the timestamp
                ts = event.timestamp(None)
                if ts:
                    # convert the timestamp into a string, or (none)
                    if self.tz:
                        ts = ts.astimezone(self.tz)
                    timestamp = ts.strftime("%d %b %Y %H:%M:%S %Z")
                else:
                    timestamp = "(unknown)"
                # get the source
                source = event.source("")
                # get the origin
                origin = event.origin("")
                # get the message
                message = event.message("")
                # display
                print "%s [%s] %s" % (timestamp, origin, message)
                if self.longfmt:
                    fields = event.fields()
                    for fieldid,value in sorted(fields, key=lambda x: (x[0].name,x[0].type)):
                        if self.fields and fieldid not in self.fields:
                            continue
                        print "\t%s=%s" % (fieldid.name, value)
            print ""
            print "found %i matches in %.3f seconds." % (len(result.events), result.stats.runtime.total_seconds())
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
