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

import sys, traceback
from terane.toolbox.admin.action import ActionMap,Action
from terane.toolbox.admin.sink.create import CreateCassandraSinkCommand
from terane.toolbox.admin.sink.delete import DeleteSinkCommand
from terane.toolbox.admin.sink.list import ListSinksCommand
from terane.toolbox.admin.sink.show import ShowSinkCommand
from terane.settings import Option, LongOption, Switch, ConfigureError
from terane.loggers import getLogger

logger = getLogger('terane.toolbox.admin')

actions = ActionMap(usage="[OPTIONS...] COMMAND", description="Terane cluster administrative commands", section="admin", options=[
    Option("H", "host", override="host", help="Connect to terane server HOST", metavar="HOST"),
    Option("u", "username", override="username", help="Authenticate with username USER", metavar="USER"),
    Option("p", "password", override="password", help="Authenticate with password PASS", metavar="PASS"),
    Switch("P", "prompt-password", override="prompt password", help="Prompt for a password"),
    LongOption("log-config", override="log config file", help="use logging configuration file FILE", metavar="FILE"),
    Switch("d", "debug", override="debug", help="Print debugging information")], actions=[
    Action("sink", usage="COMMAND", description="Manipulate sinks in a Terane cluster", actions=[
        Action("create", usage="TYPE", description="Create a sink of the specified TYPE", actions=[
            Action("cassandra", callback=CreateCassandraSinkCommand(),
                usage="[OPTIONS...] NAME",
                description="Create a Cassandra sink with the specified NAME", options=[
                Option('f', "flush-interval", override="flush interval", help="Use flush interval MILLIS", metavar="MILLIS")]),
            ]),
        Action("delete", callback=DeleteSinkCommand(),
            usage="[OPTIONS...] NAME",
            description="Delete the sink with the specified NAME"),
        Action("list", callback=ListSinksCommand(),
            usage="[OPTIONS...]",
            description="List all sinks in the cluster"),
        Action("show", callback=ShowSinkCommand(),
            usage="[OPTIONS...] NAME",
            description="Describe the sink with the specified NAME")
        ])
    ])

def admin_main():
    try:
        action = actions.parse()
        return action.run()
    except ConfigureError, e:
        print >> sys.stderr, "%s: %s" % (actions.settings.appname, e)
    except Exception, e:
        print >> sys.stderr, "\nUnhandled Exception:\n%s\n---\n%s" % (e,traceback.format_exc())
    sys.exit(1)
