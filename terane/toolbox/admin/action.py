# Copyright 2010-2014 Michael Frank <msfrank@syntaxjockey.com>
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

from terane.settings import Settings, ConfigureError

class ActionBase(object):

    def __init__(self):
        self.children = dict()

    def _init(self, settings, options, actions):
        for option in options:
            settings.add(option)
        for action in actions:
            if not isinstance(action, Action):
                raise ConfigureError("invalid action %s" % str(action))
            if action.name in self.children:
                raise ConfigureError("action %s already exists" % action.name)
            self.children[action.name] = action
            childsettings = settings.addSubcommand(action.name, action.usage, action.description)
            action._init(childsettings, action.options, action.actions)

class ActionMap(ActionBase):

    def __init__(self, usage, description, section=None, options=list(), actions=list()):
        ActionBase.__init__(self)
        self.settings = Settings(usage=usage, description=description, section=section)
        self.options = options
        self.actions = actions
        self.callback = None
        self._init(self.settings, self.options, self.actions)

    def parse(self, *args, **kwargs):
        ns = self.settings.parse(*args, **kwargs)
        action = self
        name = ns.popStack()
        while name is not None:
            action = action.children[name]
            name = ns.popStack()
        callback = action.callback
        if callback is None:
            raise ConfigureError("no action specified.  see --help for usage.")
        return callback(ns)

class Action(ActionBase):
    def __init__(self, name, callback=None, usage=None, description=None, options=list(), actions=list()):
        ActionBase.__init__(self)
        self.name = name
        self.callback = callback
        self.usage = usage
        self.description = description
        self.options = options
        self.actions = actions
