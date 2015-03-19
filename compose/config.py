import os
import yaml
import six


DOCKER_CONFIG_KEYS = [
    'cap_add',
    'cap_drop',
    'cpu_shares',
    'command',
    'detach',
    'dns',
    'dns_search',
    'domainname',
    'entrypoint',
    'env_file',
    'environment',
    'hostname',
    'image',
    'labels',
    'links',
    'mem_limit',
    'net',
    'ports',
    'privileged',
    'restart',
    'stdin_open',
    'tty',
    'user',
    'volumes',
    'volumes_from',
    'working_dir',
]

ALLOWED_KEYS = DOCKER_CONFIG_KEYS + [
    'build',
    'expose',
    'external_links',
    'name',
]

DOCKER_CONFIG_HINTS = {
    'cpu_share' : 'cpu_shares',
    'link'      : 'links',
    'port'      : 'ports',
    'privilege' : 'privileged',
    'priviliged': 'privileged',
    'privilige' : 'privileged',
    'volume'    : 'volumes',
    'workdir'   : 'working_dir',
}


def load(filename):
    working_dir = os.path.dirname(filename)
    return from_dictionary(load_yaml(filename), working_dir=working_dir)


def load_yaml(filename):
    try:
        with open(filename, 'r') as fh:
            return yaml.safe_load(fh)
    except IOError as e:
        raise ConfigurationError(six.text_type(e))


def from_dictionary(dictionary, working_dir=None):
    service_dicts = []

    for service_name, service_dict in list(dictionary.items()):
        if not isinstance(service_dict, dict):
            raise ConfigurationError('Service "%s" doesn\'t have any configuration options. All top level keys in your docker-compose.yml must map to a dictionary of configuration options.' % service_name)
        service_dict = make_service_dict(service_name, service_dict, working_dir=working_dir)
        service_dicts.append(service_dict)

    return service_dicts


def make_service_dict(name, options, working_dir=None):
    service_dict = options.copy()
    service_dict['name'] = name
    service_dict = resolve_environment(service_dict, working_dir=working_dir)
    return process_container_options(service_dict, working_dir=working_dir)


def process_container_options(service_dict, working_dir=None):
    for k in service_dict:
        if k not in ALLOWED_KEYS:
            msg = "Unsupported config option for %s service: '%s'" % (service_dict['name'], k)
            if k in DOCKER_CONFIG_HINTS:
                msg += " (did you mean '%s'?)" % DOCKER_CONFIG_HINTS[k]
            raise ConfigurationError(msg)

    return service_dict


def parse_links(links):
    return dict(parse_link(l) for l in links)


def parse_link(link):
    if ':' in link:
        source, alias = link.split(':', 1)
        return (alias, source)
    else:
        return (link, link)


def get_env_files(options, working_dir=None):
    if 'env_file' not in options:
        return {}

    if working_dir is None:
        raise Exception("No working_dir passed to get_env_files()")

    env_files = options.get('env_file', [])
    if not isinstance(env_files, list):
        env_files = [env_files]

    return [expand_path(working_dir, path) for path in env_files]


def resolve_environment(service_dict, working_dir=None):
    service_dict = service_dict.copy()

    if 'environment' not in service_dict and 'env_file' not in service_dict:
        return service_dict

    env = {}

    if 'env_file' in service_dict:
        for f in get_env_files(service_dict, working_dir=working_dir):
            env.update(env_vars_from_file(f))
        del service_dict['env_file']

    env.update(parse_environment(service_dict.get('environment')))
    env = dict(resolve_env_var(k, v) for k, v in six.iteritems(env))

    service_dict['environment'] = env
    return service_dict

def parse_environment(environment):
    if not environment:
        return {}

    if isinstance(environment, list):
        return dict(split_env(e) for e in environment)

    if isinstance(environment, dict):
        return environment

    raise ConfigurationError(
        "environment \"%s\" must be a list or mapping," %
        environment
    )

def split_env(env):
    if '=' in env:
        return env.split('=', 1)
    else:
        return env, None


def resolve_env_var(key, val):
    if val is not None:
        return key, val
    elif key in os.environ:
        return key, os.environ[key]
    else:
        return key, ''


def env_vars_from_file(filename):
    """
    Read in a line delimited file of environment variables.
    """
    if not os.path.exists(filename):
        raise ConfigurationError("Couldn't find env file: %s" % filename)
    env = {}
    for line in open(filename, 'r'):
        line = line.strip()
        if line and not line.startswith('#'):
            k, v = split_env(line)
            env[k] = v
    return env


def expand_path(working_dir, path):
    return os.path.abspath(os.path.join(working_dir, path))


class ConfigurationError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
