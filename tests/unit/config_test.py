import os
import mock
from .. import unittest

from compose import config


class ConfigTest(unittest.TestCase):
    def test_from_dictionary(self):
        config_dict = config.from_dictionary({
            'version': '1.1',
            'project': 'foo',
            'services': {
                'foo': {'image': 'busybox'},
                'bar': {'environment': ['FOO=1']},
            }
        })

        self.assertEqual(config_dict['version'], '1.1')
        self.assertEqual(config_dict['project'], 'foo')
        self.assertEqual(
            sorted(config_dict['services'], key=lambda d: d['name']),
            sorted([
                {
                    'name': 'bar',
                    'environment': {'FOO': '1'},
                },
                {
                    'name': 'foo',
                    'image': 'busybox',
                }
            ])
        )

    def test_from_dictionary_fallback_1_0(self):
        config_dict = config.from_dictionary({
            'foo': {'image': 'busybox'},
            'bar': {'environment': ['FOO=1']},
        })

        self.assertEqual(config_dict['version'], '1.0')
        self.assertIsNone(config_dict['project'])
        self.assertEqual(
            sorted(config_dict['services'], key=lambda d: d['name']),
            sorted([
                {
                    'name': 'bar',
                    'environment': {'FOO': '1'},
                },
                {
                    'name': 'foo',
                    'image': 'busybox',
                }
            ])
        )

    def test_from_dictionary_fallback_service_version(self):
        config_dict = config.from_dictionary({
            'version': {'image': 'busybox'},
        })

        self.assertEqual(
            sorted(config_dict['services'], key=lambda d: d['name']),
            sorted([
                {
                    'name': 'version',
                    'image': 'busybox',
                }
            ])
        )

    def test_from_dictionary_throws_error_when_wrong_version(self):
        with self.assertRaises(config.ConfigurationError):
            config.from_dictionary({
                'version': 'foo'
            })

    def test_from_dictionary_throws_error_when_version_to_hight(self):
        with self.assertRaises(config.ConfigurationError):
            config.from_dictionary({
                'version': '99.0'
            })

    def test_from_dictionary_throws_error_when_missing_service(self):
        with self.assertRaises(config.ConfigurationError):
            config.from_dictionary({
                'version': '1.0'
            })

    def test_from_dictionary_throws_error_when_wrong_project(self):
        with self.assertRaises(config.ConfigurationError):
            config.from_dictionary({
                'version': '1.1',
                'project': ['foo']
            })

    def test_from_dictionary_with_project_in_wrong_version(self):
        config_dict = config.from_dictionary({
            'version': '1.0',
            'project': 'foo',
            'services': {}
        })
        self.assertIsNone(config_dict['project'])

    def test_from_dictionary_throws_error_when_services_not_dict(self):
        with self.assertRaises(config.ConfigurationError):
            config.from_dictionary({
                'version': '1.0',
                'services': 'foo'
            })

    def test_from_dictionary_throws_error_when_service_not_dict(self):
        with self.assertRaises(config.ConfigurationError):
            config.from_dictionary({
                'version': '1.0',
                'services': {
                    'web': 'busybox:latest',
                }
            })

    def test_config_validation(self):
        self.assertRaises(
            config.ConfigurationError,
            lambda: config.make_service_dict('foo', {'port': ['8000']})
        )
        config.make_service_dict('foo', {'ports': ['8000']})


class MergeVolumesTest(unittest.TestCase):
    def test_empty(self):
        service_dict = config.merge_service_dicts({}, {})
        self.assertNotIn('volumes', service_dict)

    def test_no_override(self):
        service_dict = config.merge_service_dicts(
            {'volumes': ['/foo:/code', '/data']},
            {},
        )
        self.assertEqual(set(service_dict['volumes']), set(['/foo:/code', '/data']))

    def test_no_base(self):
        service_dict = config.merge_service_dicts(
            {},
            {'volumes': ['/bar:/code']},
        )
        self.assertEqual(set(service_dict['volumes']), set(['/bar:/code']))

    def test_override_explicit_path(self):
        service_dict = config.merge_service_dicts(
            {'volumes': ['/foo:/code', '/data']},
            {'volumes': ['/bar:/code']},
        )
        self.assertEqual(set(service_dict['volumes']), set(['/bar:/code', '/data']))

    def test_add_explicit_path(self):
        service_dict = config.merge_service_dicts(
            {'volumes': ['/foo:/code', '/data']},
            {'volumes': ['/bar:/code', '/quux:/data']},
        )
        self.assertEqual(set(service_dict['volumes']), set(['/bar:/code', '/quux:/data']))

    def test_remove_explicit_path(self):
        service_dict = config.merge_service_dicts(
            {'volumes': ['/foo:/code', '/quux:/data']},
            {'volumes': ['/bar:/code', '/data']},
        )
        self.assertEqual(set(service_dict['volumes']), set(['/bar:/code', '/data']))

    def test_merge_build_or_image_no_override(self):
        self.assertEqual(
            config.merge_service_dicts({'build': '.'}, {}),
            {'build': '.'},
        )

        self.assertEqual(
            config.merge_service_dicts({'image': 'redis'}, {}),
            {'image': 'redis'},
        )

    def test_merge_build_or_image_override_with_same(self):
        self.assertEqual(
            config.merge_service_dicts({'build': '.'}, {'build': './web'}),
            {'build': './web'},
        )

        self.assertEqual(
            config.merge_service_dicts({'image': 'redis'}, {'image': 'postgres'}),
            {'image': 'postgres'},
        )

    def test_merge_build_or_image_override_with_other(self):
        self.assertEqual(
            config.merge_service_dicts({'build': '.'}, {'image': 'redis'}),
            {'image': 'redis'}
        )

        self.assertEqual(
            config.merge_service_dicts({'image': 'redis'}, {'build': '.'}),
            {'build': '.'}
        )


class MergeListsTest(unittest.TestCase):
    def test_empty(self):
        service_dict = config.merge_service_dicts({}, {})
        self.assertNotIn('ports', service_dict)

    def test_no_override(self):
        service_dict = config.merge_service_dicts(
            {'ports': ['10:8000', '9000']},
            {},
        )
        self.assertEqual(set(service_dict['ports']), set(['10:8000', '9000']))

    def test_no_base(self):
        service_dict = config.merge_service_dicts(
            {},
            {'ports': ['10:8000', '9000']},
        )
        self.assertEqual(set(service_dict['ports']), set(['10:8000', '9000']))

    def test_add_item(self):
        service_dict = config.merge_service_dicts(
            {'ports': ['10:8000', '9000']},
            {'ports': ['20:8000']},
        )
        self.assertEqual(set(service_dict['ports']), set(['10:8000', '9000', '20:8000']))


class MergeStringsOrListsTest(unittest.TestCase):
    def test_no_override(self):
        service_dict = config.merge_service_dicts(
            {'dns': '8.8.8.8'},
            {},
        )
        self.assertEqual(set(service_dict['dns']), set(['8.8.8.8']))

    def test_no_base(self):
        service_dict = config.merge_service_dicts(
            {},
            {'dns': '8.8.8.8'},
        )
        self.assertEqual(set(service_dict['dns']), set(['8.8.8.8']))

    def test_add_string(self):
        service_dict = config.merge_service_dicts(
            {'dns': ['8.8.8.8']},
            {'dns': '9.9.9.9'},
        )
        self.assertEqual(set(service_dict['dns']), set(['8.8.8.8', '9.9.9.9']))

    def test_add_list(self):
        service_dict = config.merge_service_dicts(
            {'dns': '8.8.8.8'},
            {'dns': ['9.9.9.9']},
        )
        self.assertEqual(set(service_dict['dns']), set(['8.8.8.8', '9.9.9.9']))


class EnvTest(unittest.TestCase):
    def test_parse_environment_as_list(self):
        environment = [
            'NORMAL=F1',
            'CONTAINS_EQUALS=F=2',
            'TRAILING_EQUALS=',
        ]
        self.assertEqual(
            config.parse_environment(environment),
            {'NORMAL': 'F1', 'CONTAINS_EQUALS': 'F=2', 'TRAILING_EQUALS': ''},
        )

    def test_parse_environment_as_dict(self):
        environment = {
            'NORMAL': 'F1',
            'CONTAINS_EQUALS': 'F=2',
            'TRAILING_EQUALS': None,
        }
        self.assertEqual(config.parse_environment(environment), environment)

    def test_parse_environment_invalid(self):
        with self.assertRaises(config.ConfigurationError):
            config.parse_environment('a=b')

    def test_parse_environment_empty(self):
        self.assertEqual(config.parse_environment(None), {})

    @mock.patch.dict(os.environ)
    def test_resolve_environment(self):
        os.environ['FILE_DEF'] = 'E1'
        os.environ['FILE_DEF_EMPTY'] = 'E2'
        os.environ['ENV_DEF'] = 'E3'

        service_dict = config.make_service_dict(
            'foo', {
                'environment': {
                    'FILE_DEF': 'F1',
                    'FILE_DEF_EMPTY': '',
                    'ENV_DEF': None,
                    'NO_DEF': None
                },
            },
        )

        self.assertEqual(
            service_dict['environment'],
            {'FILE_DEF': 'F1', 'FILE_DEF_EMPTY': '', 'ENV_DEF': 'E3', 'NO_DEF': ''},
        )

    def test_env_from_file(self):
        service_dict = config.make_service_dict(
            'foo',
            {'env_file': 'one.env'},
            'tests/fixtures/env',
        )
        self.assertEqual(
            service_dict['environment'],
            {'ONE': '2', 'TWO': '1', 'THREE': '3', 'FOO': 'bar'},
        )

    def test_env_from_multiple_files(self):
        service_dict = config.make_service_dict(
            'foo',
            {'env_file': ['one.env', 'two.env']},
            'tests/fixtures/env',
        )
        self.assertEqual(
            service_dict['environment'],
            {'ONE': '2', 'TWO': '1', 'THREE': '3', 'FOO': 'baz', 'DOO': 'dah'},
        )

    def test_env_nonexistent_file(self):
        options = {'env_file': 'nonexistent.env'}
        self.assertRaises(
            config.ConfigurationError,
            lambda: config.make_service_dict('foo', options, 'tests/fixtures/env'),
        )

    @mock.patch.dict(os.environ)
    def test_resolve_environment_from_file(self):
        os.environ['FILE_DEF'] = 'E1'
        os.environ['FILE_DEF_EMPTY'] = 'E2'
        os.environ['ENV_DEF'] = 'E3'
        service_dict = config.make_service_dict(
            'foo',
            {'env_file': 'resolve.env'},
            'tests/fixtures/env',
        )
        self.assertEqual(
            service_dict['environment'],
            {'FILE_DEF': 'F1', 'FILE_DEF_EMPTY': '', 'ENV_DEF': 'E3', 'NO_DEF': ''},
        )


class ExtendsTest(unittest.TestCase):
    def test_extends(self):
        config_dict = config.load('tests/fixtures/extends/docker-compose.yml')

        service_dicts = sorted(
            config_dict['services'],
            key=lambda sd: sd['name'],
        )

        self.assertEqual(service_dicts, [
            {
                'name': 'mydb',
                'image': 'busybox',
                'command': 'sleep 300',
            },
            {
                'name': 'myweb',
                'image': 'busybox',
                'command': 'sleep 300',
                'links': ['mydb:db'],
                'environment': {
                    "FOO": "1",
                    "BAR": "2",
                    "BAZ": "2",
                },
            }
        ])

    def test_nested(self):
        config_dict = config.load('tests/fixtures/extends/nested.yml')

        self.assertEqual(config_dict['services'], [
            {
                'name': 'myweb',
                'image': 'busybox',
                'command': '/bin/true',
                'environment': {
                    "FOO": "2",
                    "BAR": "2",
                },
            },
        ])

    def test_circular(self):
        try:
            config.load('tests/fixtures/extends/circle-1.yml')
            raise Exception("Expected config.CircularReference to be raised")
        except config.CircularReference as e:
            self.assertEqual(
                [(os.path.basename(filename), service_name) for (filename, service_name) in e.trail],
                [
                    ('circle-1.yml', 'web'),
                    ('circle-2.yml', 'web'),
                    ('circle-1.yml', 'web'),
                ],
            )

    def test_extends_validation(self):
        dictionary = {'extends': None}

        def load_config():
            return config.make_service_dict('myweb', dictionary, working_dir='tests/fixtures/extends')

        self.assertRaisesRegexp(config.ConfigurationError, 'dictionary', load_config)

        dictionary['extends'] = {}
        self.assertRaises(config.ConfigurationError, load_config)

        dictionary['extends']['file'] = 'common.yml'
        self.assertRaisesRegexp(config.ConfigurationError, 'service', load_config)

        dictionary['extends']['service'] = 'web'
        self.assertIsInstance(load_config(), dict)

        dictionary['extends']['what'] = 'is this'
        self.assertRaisesRegexp(config.ConfigurationError, 'what', load_config)

    def test_blacklisted_options(self):
        def load_config():
            return config.make_service_dict('myweb', {
                'extends': {
                    'file': 'whatever',
                    'service': 'web',
                }
            }, '.')

        with self.assertRaisesRegexp(config.ConfigurationError, 'links'):
            other_config = {'web': {'links': ['db']}}

            with mock.patch.object(config, 'load_yaml', return_value=other_config):
                print load_config()

        with self.assertRaisesRegexp(config.ConfigurationError, 'volumes_from'):
            other_config = {'web': {'volumes_from': ['db']}}

            with mock.patch.object(config, 'load_yaml', return_value=other_config):
                print load_config()

        with self.assertRaisesRegexp(config.ConfigurationError, 'net'):
            other_config = {'web': {'net': 'container:db'}}

            with mock.patch.object(config, 'load_yaml', return_value=other_config):
                print load_config()

        other_config = {'web': {'net': 'host'}}

        with mock.patch.object(config, 'load_yaml', return_value=other_config):
            print load_config()

    def test_volume_path(self):
        dicts = config.load('tests/fixtures/volume-path/docker-compose.yml')

        paths = [
            '%s:/foo' % os.path.abspath('tests/fixtures/volume-path/common/foo'),
            '%s:/bar' % os.path.abspath('tests/fixtures/volume-path/bar'),
        ]

        self.assertEqual(set(dicts['services'][0]['volumes']), set(paths))
