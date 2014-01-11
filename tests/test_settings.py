from terane.settings import *

class TestSettings(object):

    def test_settings_option(self):
        settings = Settings("usage", "description", section="test", appname="test", confbase="./")
        settings.addOption("o", "option", "test option")
        ns = settings.parse(argv=['test', '-o', 'foo'])
        assert ns.section('test').getString('test option') == 'foo'
        ns = settings.parse(argv=['test', '--option', 'bar'])
        assert ns.section('test').getString('test option') == 'bar'

    def test_settings_switch(self):
        settings = Settings("usage", "description", section="test", appname="test", confbase="./")
        settings.addSwitch("s", "switch", "test switch")
        ns = settings.parse(argv=['test', '-s'])
        assert ns.section('test').getBoolean('test switch') == True
        ns = settings.parse(argv=['test', '--switch'])
        assert ns.section('test').getBoolean('test switch') == True

    def test_settings_switch_reverse(self):
        settings = Settings("usage", "description", section="test", appname="test", confbase="./")
        settings.addSwitch("s", "switch", "test switch", reverse=True)
        ns = settings.parse(argv=['test', '-s'])
        assert ns.section('test').getBoolean('test switch') == False
        ns = settings.parse(argv=['test', '--switch'])
        assert ns.section('test').getBoolean('test switch') == False

    def test_load_config_file(self):
        settings = Settings("usage", "description", section="test", appname="test-config", confbase="./tests")
        ns = settings.parse(argv=['test', '-c', './tests/test-config.conf'])
        assert ns.section('test').getString('string') == 'hello world'
        assert ns.section('test').getInt('int') == 42
        assert ns.section('test').getFloat('float') == 3.14
        assert ns.section('test').getBoolean('boolean') == False
        assert ns.section('test').getPath('path') == '/bin/true'
        assert ns.section('test').getList('list', int) == [1, 2, 3]
        ns = settings.parse(argv=['test'])
        assert ns.section('test').getString('string') == 'hello world'
        assert ns.section('test').getInt('int') == 42
        assert ns.section('test').getFloat('float') == 3.14
        assert ns.section('test').getBoolean('boolean') == False
        assert ns.section('test').getPath('path') == '/bin/true'
        assert ns.section('test').getList('list', int) == [1, 2, 3]

    def test_subcommand_one_level(self):
        settings = Settings("usage", "description", section="test")
        settings.addLongOption("option", "test option")
        cmd1 = settings.addSubcommand("cmd1", "usage", "description")
        cmd1.addLongOption("cmd1-option", "cmd1 option")
        ns = settings.parse(argv=['test', '--option', 'foo', 'cmd1', '--cmd1-option', 'bar'])
        assert ns.section('test').getString('test option') == 'foo'
        assert ns.section('test:cmd1').getString('cmd1 option') == 'bar'

    def test_subcommand_multi_level(self):
        settings = Settings("usage", "description", section="test")
        child = settings.addSubcommand("child", "usage", "description")
        gchild = child.addSubcommand("grandchild", "usage", "description")
        ggchild = gchild.addSubcommand("great-grandchild", "usage", "description")
        ggchild.addLongOption("option", "option")
        ns = settings.parse(argv=['test', 'child', 'grandchild', 'great-grandchild', '--option', 'foo'])
        assert ns.section('test:child:grandchild:great-grandchild').getString('option') == 'foo'
