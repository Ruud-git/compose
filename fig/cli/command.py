from __future__ import unicode_literals
from __future__ import absolute_import
from docker import Client
from docker import tls
from requests.exceptions import ConnectionError
import errno
import logging
import os
import re
import yaml
import six
import ssl

from ..project import Project
from ..service import ConfigError
from .docopt_command import DocoptCommand
from .utils import docker_url, call_silently, is_mac, is_ubuntu
from . import verbose_proxy
from . import errors
from .. import __version__

log = logging.getLogger(__name__)


class Command(DocoptCommand):
    base_dir = '.'

    def dispatch(self, *args, **kwargs):
        try:
            super(Command, self).dispatch(*args, **kwargs)
        except ConnectionError:
            if call_silently(['which', 'docker']) != 0:
                if is_mac():
                    raise errors.DockerNotFoundMac()
                elif is_ubuntu():
                    raise errors.DockerNotFoundUbuntu()
                else:
                    raise errors.DockerNotFoundGeneric()
            elif call_silently(['which', 'docker-osx']) == 0:
                raise errors.ConnectionErrorDockerOSX()
            else:
                raise errors.ConnectionErrorGeneric(self.get_client().base_url)

    def perform_command(self, options, handler, command_options):
        explicit_config_path = options.get('--file') or os.environ.get('FIG_FILE')
        project = self.get_project(
            self.get_config_path(explicit_config_path),
            project_name=options.get('--project-name'),
            verbose=options.get('--verbose'))

        handler(project, command_options)

    def get_client(self, verbose=False):
        if os.environ.get('FIG_TLS_PATH') is not None:
            tls_path = os.environ.get('FIG_TLS_PATH')
            tls_config = tls.TLSConfig(
                ssl_version=ssl.PROTOCOL_TLSv1,
                verify=True,
                client_cert=(tls_path + '/cert.pem', tls_path + '/key.pem'),
                ca_cert=tls_path + '/ca.pem'
            )
            client = Client(base_url=docker_url(), tls=tls_config)
        else:
            client = Client(docker_url())
        if verbose:
            version_info = six.iteritems(client.version())
            log.info("Fig version %s", __version__)
            log.info("Docker base_url: %s", client.base_url)
            log.info("Docker version: %s",
                     ", ".join("%s=%s" % item for item in version_info))
            return verbose_proxy.VerboseProxy('docker', client)
        return client

    def get_config(self, config_path):
        try:
            with open(config_path, 'r') as fh:
                return yaml.safe_load(fh)
        except IOError as e:
            if e.errno == errno.ENOENT:
                raise errors.FigFileNotFound(os.path.basename(e.filename))
            raise errors.UserError(six.text_type(e))

    def get_project(self, config_path, project_name=None, verbose=False):
        try:
            return Project.from_config(
                self.get_project_name(config_path, project_name),
                self.get_config(config_path),
                self.get_client(verbose=verbose))
        except ConfigError as e:
            raise errors.UserError(six.text_type(e))

    def get_project_name(self, config_path, project_name=None):
        def normalize_name(name):
            return re.sub(r'[^a-zA-Z0-9]', '', name)

        if project_name is not None:
            return normalize_name(project_name)

        project = os.path.basename(os.path.dirname(os.path.abspath(config_path)))
        if project:
            return normalize_name(project)

        return 'default'

    def get_config_path(self, file_path=None):
        if file_path:
            return os.path.join(self.base_dir, file_path)

        if os.path.exists(os.path.join(self.base_dir, 'fig.yaml')):
            log.warning("Fig just read the file 'fig.yaml' on startup, rather "
                        "than 'fig.yml'")
            log.warning("Please be aware that fig.yml the expected extension "
                        "in most cases, and using .yaml can cause compatibility "
                        "issues in future")

            return os.path.join(self.base_dir, 'fig.yaml')

        return os.path.join(self.base_dir, 'fig.yml')
