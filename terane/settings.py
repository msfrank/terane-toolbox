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

import os, sys, getopt
from ConfigParser import RawConfigParser
from terane.loggers import getLogger
from terane import versionstring

logger = getLogger('terane.settings')

class ConfigureError(Exception):
    """
    Configuration parsing failed.
    """
    pass

class Option(object):
    """
    A command line option.
    """
    def __init__(self, shortname, longname, override, section=None, help=None, metavar=None):
        self.shortname = shortname
        self.shortident = "%s:" % shortname
        self.longname = longname
        self.longident = "%s=" % longname
        self.section = section
        self.override = override
        self.help = help
        self.metavar = metavar

class ShortOption(Option):
    """
    A command line option with only a short name.
    """
    def __init__(self, shortname, override, section=None, help=None, metavar=None):
        Option.__init__(self, shortname, '', override, section, help, metavar)

class LongOption(Option):
    """
    A command line option with only a long name.
    """
    def __init__(self, longname, override, section=None, help=None, metavar=None):
        Option.__init__(self, '', longname, override, section, help, metavar)

class Switch(Option):
    """
    A command line switch.
    """
    def __init__(self, shortname, longname, override, section=None, reverse=False, help=None):
        Option.__init__(self, shortname, longname, override, section, help)
        self.shortident = shortname
        self.longident = longname
        self.reverse = reverse

class ShortSwitch(Switch):
    """
    A command line switch with only a short name.
    """
    def __init__(self, shortname, override, section=None, reverse=False, help=None):
        Switch.__init__(self, shortname, '', override, section, reverse, help)

class LongSwitch(Switch):
    """
    A command line switch with only a long name.
    """
    def __init__(self, longname, override, section=None, reverse=False, help=None):
        Switch.__init__(self, '', longname, override, section, reverse, help)

class Parser(object):
    """
    """
    def __init__(self, parent, name, usage, description, subusage):
        """
        :param parent:
        :type parent: :class:`Parser`
        :param name:
        :type name: str
        :param usage:
        :type usage: str
        :param description:
        :type description: str
        :param subusage:
        :type subusage: str
        """
        self._parent = parent
        self.name = name
        self.usage = usage
        self.description = description
        self.subusage = subusage
        self._subcommands = {}
        self._options = {}
        self._optslist = []

    def addSubcommand(self, name, usage, description, subusage='Available subcommands:'):
        """
        Add a subcommand to the parser.

        :param name:
        :type name: str
        :param usage:
        :type usage: str
        :param description:
        :type description: str
        :param subusage:
        :type subusage: str
        """
        if name in self._subcommands:
            raise ConfigureError("subcommand '%s' is already defined" % name)
        subcommand = Parser(self, name, usage, description, subusage)
        self._subcommands[name] = subcommand
        return subcommand

    def _lookupSection(self):
        sections = list()
        parser = self
        while parser is not None:
            sections.insert(0, parser.name)
            parser = parser._parent
        return ':'.join(sections)

    def add(self, o):
        """
        Add a command-line option or switch.

        :param o: o
        :type o: :class:`Option`
        """
        if not isinstance(o, Option):
            raise TypeError("%s is not an instance of type Option" % o)
        if o.shortname in self._options:
            raise RuntimeError("-%s is already defined" % o.shortname)
        if o.longname in self._options:
            raise RuntimeError("--%s is already defined" % o.longname)
        if o.section is None:
            o.section = self._lookupSection()
        self._options["-%s" % o.shortname] = o
        self._options["--%s" % o.longname] = o
        self._optslist.append(o)

    def addOption(self, shortname, longname, override, section=None, help=None, metavar=None):
        """
        Add a command-line option to be parsed.  An option (as opposed to a switch)
        is required to have an argument.

        :param shortname: the one letter option name.
        :type shortname: str
        :param longname: the long option name.
        :type longname: str
        :param override: Override the specified section key.
        :type override: str
        :param section: Override the key in the specified section.
        :type section: str
        :param help: The help string, displayed in --help output.
        :type help: str
        :param metavar: The variable displayed in the help string
        :type metavar: str
        """
        self.add(Option(shortname, longname, override, section, help, metavar))

    def addShortOption(self, shortname, override, section=None, help=None, metavar=None):
        self.add(ShortOption(shortname, override, section, help, metavar))

    def addLongOption(self, longname, override, section=None, help=None, metavar=None):
        self.add(LongOption(longname, override, section, help, metavar))

    def addSwitch(self, shortname, longname, override, section=None, reverse=False, help=None):
        """
        Add a command-line switch to be parsed.  A switch (as opposed to an option)
        has no argument.

        :param shortname: the one letter option name.
        :type shortname: str
        :param longname: the long option name.
        :type longname: str
        :param override: Override the specified section key.
        :type override: str
        :param section: Override the key in the specified section.
        :type section: str
        :param reverse: If True, then the meaning of the switch is reversed.
        :type reverse: bool
        :param help: The help string, displayed in --help output.
        :type help: str
        """
        self.add(Switch(shortname, longname, override, section, reverse, help))

    def addShortSwitch(self, shortname, override, section=None, reverse=False, help=None):
        self.add(ShortSwitch(shortname, override, section, reverse, help))

    def addLongSwitch(self, longname, override, section=None, reverse=False, help=None):
        self.add(LongSwitch(longname, override, section, reverse, help))

    def _parse(self, argv, store):
        """
        Parse the command line specified by argv, and store the options
        in store.
        """
        shortnames = ''.join([o.shortident for o in self._optslist if o.shortname != ''])
        longnames = [o.longident for o in self._optslist if o.longname != '']
        longnames += ['help', 'version']
        if len(self._subcommands) == 0:
            opts,args = getopt.gnu_getopt(argv, shortnames, longnames)
        else:
            opts,args = getopt.getopt(argv, shortnames, longnames)
        for opt,value in opts:
            if opt == '--help': self._usage()
            if opt == '--version': self._version()
            o = self._options[opt]
            if not store.has_section(o.section):
                store.add_section(o.section)
            if isinstance(o, Switch):
                if o.reverse == True:
                    store.set(o.section, o.override, 'false')
                else:
                    store.set(o.section, o.override, 'true')
            elif isinstance(o, Option):
                store.set(o.section, o.override, value)
        if len(self._subcommands) > 0:
            if len(args) == 0:
                raise ConfigureError("no subcommand specified")
            subcommand = args[0]
            args = args[1:]
            if not subcommand in self._subcommands:
                raise ConfigureError("no subcommand named '%s'" % subcommand)
            stack,args = self._subcommands[subcommand]._parse(args, store)
            stack.insert(0, subcommand)
            return stack,args
        return [], args

    def _usage(self):
        """
        Display a usage message and exit.
        """
        commands = []
        c = self
        while c != None:
            commands = [c.name] + commands
            c = c._parent
        print "Usage: %s %s" % (' '.join(commands), self.usage)
        print 
        # display the description, if it was specified
        if self.description != None and self.description != '':
            print self.description
            print
        # display options
        if len(self._optslist) > 0:
            options = []
            maxlength = 0
            for o in self._optslist:
                spec = []
                if o.shortname != '':
                    spec.append("-%s" % o.shortname)
                if o.longname != '':
                    spec.append("--%s" % o.longname)
                if isinstance(o, Switch):
                    spec = ','.join(spec)
                elif isinstance(o, Option):
                    spec = ','.join(spec) + ' ' + o.metavar
                options.append((spec, o.help))
                if len(spec) > maxlength:
                    maxlength = len(spec)
            for spec,help in options: 
                print " %s%s" % (spec.ljust(maxlength + 4), help)
            print
        # display subcommands, if there are any
        if len(self._subcommands) > 0:
            print self.subusage
            print
            for name,parser in sorted(self._subcommands.items()):
                print " %s" % name
            print
        sys.exit(0)

    def _version(self):
        """
        Display the version and exit.
        """
        c = self
        while c._parent != None: c = c._parent
        print "%s %s" % (c.name, versionstring())
        sys.exit(0)

class Settings(Parser):
    """
    Contains configuration loaded from the configuration file and
    parsed from command-line arguments.
    """

    def __init__(self, usage, description, subusage='Available subcommands:', section=None, appname=None, confbase='/etc/terane/'):
        """
        :param usage: The usage string, displayed in --help output
        :type usage: str
        :param description: A short application description, displayed in --help output
        :type description: str
        :param subusage: If subcommands are specified, then display this message above
        :type subusage: str
        """
        self.appname = appname if appname is not None else os.path.basename(sys.argv[0])
        self._section = self.appname if section is None else section
        self._confbase = os.path.abspath(confbase)
        self._cwd = os.getcwd()
        Parser.__init__(self, None, self._section, usage, description, subusage)
        self.addOption('c', 'config-file', 'config file',
            section=self._section, help="Load configuration from FILE", metavar="FILE"
            )

    def parse(self, argv=None, needsconfig=False):
        """
        Load configuration from the configuration file and from command-line arguments.

        :param argv: The argument vector, or None to use sys.argv
        :type argv: [str]
        :param needsconfig: True if the config file must be present for the application to function.
        :type needsconfig: bool
        :returns: A :class:`Namespace` object with the parsed settings
        :rtype: :class:`Namespace`
        """
        stack = list()
        options = RawConfigParser()
        args = list()
        overrides = RawConfigParser()
        try:
            argv = argv if argv is not None else sys.argv
            overrides.add_section(self._section)
            overrides.set(self._section, 'config file', os.path.join(self._confbase, "%s.conf" % self.appname))
            # parse command line arguments
            stack,args = self._parse(argv[1:], overrides)
            # load configuration file
            config_file = overrides.get(self._section, 'config file')
            path = os.path.normpath(os.path.join(self._cwd, config_file))
            with open(path, 'r') as f:
                options.readfp(f, path)
            logger.debug("loaded settings from %s" % path)
        except getopt.GetoptError, e:
            raise ConfigureError(str(e))
        except EnvironmentError, e:
            if needsconfig:
                raise ConfigureError("failed to read configuration: %s" % e.strerror)
            logger.info("didn't load configuration: %s" % e.strerror)
        # merge command line settings with config file settings
        for section in overrides.sections():
            for name,value in overrides.items(section):
                if not options.has_section(section):
                    options.add_section(section)
                options.set(section, name, str(value))
        return Namespace(stack, options, args, self.appname, self._cwd, self._section)

class Namespace(object):
    """
    """
    def __init__(self, stack, options, args, appname, cwd, section):
        """
        :param stack:
        :type stack: [str]
        :param options:
        :type options: :class:`ConfigParser.RawConfigParser`
        :param args:
        :type args: [str]
        :param appname:
        :type appname: str
        :param cwd:
        :type cwd: str
        """
        self._stack = stack
        self._options = options
        self._args = args
        self._appname = appname
        self._cwd = cwd
        self._section = section

    @property
    def appname(self):
        return self._appname

    @property
    def cwd(self):
        return self._cwd

    @property
    def args(self):
        return list(self._args)

    def getArgs(self, *spec, **kwargs):
        """
        Returns a list containing arguments conforming to *spec.  if the number of
        command arguments is less than minimum or greater than maximum, or if any
        argument cannot be validated, ConfigureError is raised.  Any optional arguments
        which are not specified are set to None.

        :param spec: a list of validator functions
        :type spec: [callable]
        :param minimum: The number of required arguments
        :type: int
        :param maximum: The numer of required + optional arguments
        :type maxmimum: int
        :param names: a list of argument names corresponding to each validator
        :type names: [str]
        :returns: a list containing arguments conforming to spec
        :rtype: [object]
        """
        try:
            minimum = kwargs['minimum']
        except:
            minimum = None
        try:
            maximum = kwargs['maximum']
        except:
            maximum = None
        try:
            names = kwargs['names']
        except:
            names = None
        if maximum != None and len(self._args) > maximum:
            raise ConfigureError("extra trailing arguments")
        args = [None for _ in range(len(spec))]
        for i in range(len(spec)):
            try:
                validator = spec[i]
                args[i] = validator(self._args[i])
            except IndexError:
                if minimum == None or i < minimum:
                    if names != None:
                        raise ConfigureError("missing argument " + names[i])
                    raise ConfigureError("missing argument")
            except Exception, e:
                if names != None:
                    raise ConfigureError("failed to parse argument %s: %s" % (names[i], str(e)))
                raise ConfigureError("failed to parse argument: %s" % str(e))
        return args

    def popStack(self):
        if len(self._stack) > 0:
            return self._stack.pop(0)
        return None

    def hasSection(self, name):
        """
        Returns True if the specified section exists, otherwise False.

        :param name: The section name.
        :type name: str
        :returns: True or False.
        :rtype: [bool]
        """
        return self._options.has_section(name)

    def section(self, name=None):
        """
        Get the section with the specified name, or the section named appname
        if name is None.  Note if the section does not exist, this method still
        doesn't fail, it returns an empty Section.

        :param name: The section name.
        :type name: str
        :returns: The specified section.
        :rtype: :class:`Section`
        """
        name = self._section if name is None else name
        return Section(name, self._options, self._cwd)

    def sections(self):
        """
        Return a list of all sections.

        :returns: A list of all sections.
        :rtype: :[class:`Section`]
        """
        sections = []
        for name in self._options.sections():
            sections.append(Section(name, self._options, self._cwd))
        return sections

    def sectionsLike(self, startsWith):
        """
        Return a list of all sections which start with the specified prefix.

        :param startsWith: The section name prefix.
        :type name: str
        :returns: A list of matching sections.
        :rtype: [:class:`Section`]
        """
        sections = []
        for name in [s for s in self._options.sections() if s.startswith(startsWith)]:
            sections.append(Section(name, self._options, self._cwd))
        return sections

class Section(object):
    """
    A group of configuration values which share a common purpose.

    :param name: The name of the section.
    :type name: str
    :param options: The parent :class:`Settings` instance.
    :type options: :class:`ConfigParser.RawConfigParser`
    :param cwd: the current working directory
    :type cwd: str
    """

    def __init__(self, name, options, cwd):
        self.name = name
        self._options = options
        self._cwd = cwd

    def getString(self, name, default=None):
        """
        Returns the configuration value associated with the specified name,
        coerced into a str.  If there is no configuration value in the section
        called `name`, then return the value specified by `default`.  Note that
        `default` is returned unmodified (i.e. not coerced into a string).
        This makes it easy to detect if a configuration value is not present
        by setting `default` to None.

        :param name: The configuration setting name.
        :type name: str
        :param default: The value to return if a value is not found.
        :returns: The string value, or the default value.
        """
        if self.name == None or not self._options.has_option(self.name, name):
            return default
        s = self._options.get(self.name, name)
        if s == None:
            return default
        return s.strip()

    def getInt(self, name, default=None):
        """
        Returns the configuration value associated with the specified name,
        coerced into a int.  If there is no configuration value in the section
        called `name`, then return the value specified by `default`.  Note that
        `default` is returned unmodified (i.e. not coerced into an int).
        This makes it easy to detect if a configuration value is not present
        by setting `default` to None.

        :param name: The configuration setting name.
        :type name: str
        :param default: The value to return if a value is not found.
        :returns: The int value, or the default value.
        """
        if self.name == None or not self._options.has_option(self.name, name):
            return default
        if self._options.get(self.name, name) == None:
            return default
        return self._options.getint(self.name, name)

    def getBoolean(self, name, default=None):
        """
        Returns the configuration value associated with the specified name,
        coerced into a bool.  If there is no configuration value in the section
        called `name`, then return the value specified by `default`.  Note that
        `default` is returned unmodified (i.e. not coerced into a bool).
        This makes it easy to detect if a configuration value is not present
        by setting `default` to None.

        :param name: The configuration setting name.
        :type name: str
        :param default: The value to return if a value is not found.
        :returns: The bool value, or the default value.
        """
        if self.name == None or not self._options.has_option(self.name, name):
            return default
        if self._options.get(self.name, name) == None:
            return default
        return self._options.getboolean(self.name, name)

    def getFloat(self, name, default=None):
        """
        Returns the configuration value associated with the specified name,
        coerced into a float.  If there is no configuration value in the section
        called `name`, then return the value specified by `default`.  Note that
        `default` is returned unmodified (i.e. not coerced into a float).
        This makes it easy to detect if a configuration value is not present
        by setting `default` to None.

        :param name: The configuration setting name.
        :type name: str
        :param default: The value to return if a value is not found.
        :returns: The float value, or the default value.
        """
        if self.name == None or not self._options.has_option(self.name, name):
            return default
        if self._options.get(self.name, name) == None:
            return default
        return self._options.getfloat(self.name, name)

    def getPath(self, name, default=None):
        """
        Returns the configuration value associated with the specified name,
        coerced into a str and normalized as a filesystem absolute path.  If
        there is no configuration value in the section called `name`, then
        return the value specified by `default`.  Note that `default` is
        returned unmodified (i.e. not coerced into a string).  This makes it
        easy to detect if a configuration value is not present by setting
        `default` to None.

        :param name: The configuration setting name.
        :type name: str
        :param default: The value to return if a value is not found.
        :returns: The string value, or the default value.
        """
        if self.name == None or not self._options.has_option(self.name, name):
            return default
        path = self._options.get(self.name, name)
        if path == None:
            return default
        return os.path.normpath(os.path.join(self._cwd, path))

    def getList(self, name, opttype, default=None, delimiter=','):
        """
        Returns the configuration value associated with the specified `name`,
        coerced into a list of values with the specified `type`.  If
        there is no configuration value in the section called `name`, then
        return the value specified by `default`.  Note that `default` is
        returned unmodified (i.e. not coerced into a list).  This makes it
        easy to detect if a configuration value is not present by setting
        `default` to None.

        :param name: The configuration setting name.
        :type name: str
        :param opttype: The type of each option element in the list.
        :type name: classtype
        :param default: The value to return if a value is not found.
        :param delimiter: The delimiter which separates values in the list.
        :type delimiter: str
        :returns: The string value, or the default value.
        """
        if self.name == None or not self._options.has_option(self.name, name):
            return default
        l = self._options.get(self.name, name)
        if l == None:
            return default
        try:
            return [opttype(e.strip()) for e in l.split(delimiter)]
        except Exception, e:
            raise ConfigureError("failed to parse configuration item [%s]=>%s: %s" % (
                self.name, name, e))

    def set(self, name, value):
        """
        Modify the configuration setting.  value must be a string.
        """
        if not isinstance(value, str):
            raise ConfigureError("failed to modify configuration item [%s]=>%s: value is not a string" % (
            self.name, name))
        self._options.set(self.name, name, value)

    def remove(self, name):
        """
        Remove the configuration setting.  Internally this sets the configuration
        value to None.
        """
        self._options.set(self.name, name, None)

class NodespecSettings(object):
    """
    """
    def __init__(self, pipeline):
        """
        :param pipeline: A list of Node objects
        :type pipeline: list
        """
        self._options = RawConfigParser()
        self._cwd = os.getcwd()
        self._nodes = list()
        index = 0
        for node in pipeline:
            sectionname = "node%i:%s" % (index, node.name)
            self._options.add_section(sectionname)
            for key,value in node.params.items():
                self._options.set(sectionname, key, value)
            self._nodes.append(sectionname)
            index += 1

    def hasSection(self, index):
        """
        Returns True if the specified section exists, otherwise False.

        :param index: The section index.
        :type index: int
        :returns: True or False.
        :rtype: [bool]
        """
        try:
            self._nodes[index]
            return True
        except IndexError:
            return False

    def section(self, index):
        """
        Get the section with the specified name.  Note if the section
        does not exist, this method still doesn't fail.

        :param index: The section name.
        :type index: int
        :returns: The specified section.
        :rtype: :class:`Section`
        """
        try:
            sectionname = self._nodes[index]
            return Section(sectionname, self._options, self._cwd)
        except IndexError:
            return Section(None, self._options, self._cwd)

    def sections(self):
        """
        Return a list of all sections.

        :returns: A list of all sections.
        :rtype: :[class:`Section`]
        """
        sections = []
        for sectionname in self._nodes:
            sections.append(Section(sectionname, self._options, self._cwd))
        return sections

class _UnittestSettings(Settings):
    """
    Subclass of Settings which loads configuration from a dict of dicts.  Only
    useful for unit tests.
    """
    def __init__(self, usage='', description='', appname=''):
        """
        :param usage: The usage string, displayed in --help output.
        :type usage: str
        :param description: A short application description, displayed in --help output.
        :type description: str
        :param appname: The application name.
        :type appname: str
        """
        Parser.__init__(self, appname, usage, description)
        self.appname = appname
        self._config = RawConfigParser()
        self._overrides = RawConfigParser()
        self._cwd = os.getcwd()
        self._overrides.add_section('settings')
        self._overrides.set('settings', 'config file', "/etc/terane/%s.conf" % self.appname)
        self.addOption('c', 'config-file', 'settings', 'config file',
            help="Load configuration from FILE", metavar="FILE")

    def load(self, sections, cmdline=[]):
        """
        Load the configuration from the specified dict.

        :param sections: A dict whose keys are section names, and whose values are
          dicts containing option key-value pairs.
        :type sections: dict
        :param cmdline: A list of command line arguments.  Note this list excludes
          the executable name at cmdline[0].
        :type cmdline: list
        """
        # parse command line arguments
        self._parser,self._args = self._parse(cmdline, self._overrides)
        for sectionname,kvs in sections.items():
            self._config.add_section(sectionname)
            for key,value in kvs.items():
                self._config.set(sectionname, key, value)
        # merge command line settings with config file settings
        for section in self._overrides.sections():
            for name,value in self._overrides.items(section):
                if not self._config.has_section(section):
                    self._config.add_section(section)
                self._config.set(section, name, str(value))
