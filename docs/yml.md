<!--[metadata]>
+++
title = "docker-compose.yml reference"
description = "docker-compose.yml reference"
keywords = ["fig, composition, compose,  docker"]
[menu.main]
parent="smn_compose_ref"
+++
<![end-metadata]-->


# docker-compose.yml reference

Each service defined in `docker-compose.yml` must specify exactly one of
`image` or `build`. Other keys are optional, and are analogous to their
`docker run` command-line counterparts.

As with `docker run`, options specified in the Dockerfile (e.g., `CMD`,
`EXPOSE`, `VOLUME`, `ENV`) are respected by default - you don't need to
specify them again in `docker-compose.yml`.

Values for configuration options can contain environment variables, e.g.
`image: postgres:${POSTGRES_VERSION}`. For more details, see the section on
[variable substitution](#variable-substitution).

### image

Tag, partial image ID or digest. Can be local or remote - Compose will attempt to
pull if it doesn't exist locally.

    image: ubuntu
    image: orchardup/postgresql
    image: a4bc65fd
    image: busybox@sha256:38a203e1986cf79639cfb9b2e1d6e773de84002feea2d4eb006b52004ee8502d

### build

Path to a Dockerfile or to a context containing a Dockerfile. When the
value supplied is a relative filesystem path, it is interpreted as relative
to the location of the config file.

The value supplied to this parameter can have any of the forms accepted by
the docker remote api `/build` endpoint:

* An http(s) or git URL. The resource at the other end of the URL can be
either a compressed tarball or raw Dockerfile in the case of http(s) or a
souce code repository having a Dockerfile at the root in the case of git.
To be interpreted as a remote URL the value must have one of the following
prefixes: `http://`, `https://`, `git@`, `git://` or `github.com`.

    + Examples: 
      + A git repo: `build: https://github.com/<user>/<repo>.git`. The
docker daemon clones the repo and builds from the resultant git workdir.
      + A remote tarball: `build: http://remote/context.tar.bz2` The docker
daemon downloads the context, unpacks it, and builds the image.

* The build context can also be given as a path to a single Dockerfile.
Compose will create a tar archive with that Dockerfile inside and ship it
to the docker daemon to build:

    + `build: /path/to/Dockerfile`
 
* You can also build from generated tarball contexts. The tar archive is
sent 'as is' to the daemon - Compose does not validate its contents, it
just checks to see if the supplied value points to a readable tar file.
The docker daemon supports archives compressed in the following formats:
`identity` (no compression), `gzip`, `xz` and `bzip2`.

   + `build: /path/to/localcontext.tar.gz`

* Finally, `build` can be a path to a local directory containing a Dockerfile
in it. The contents of the directory are packaged in a uncompressed tar
archive and sent to the daemon. If there's a `.dockerignore` file inside
the directory, Compose will filter the directory accordingly.

   + `build: /path/to/localdir`

Compose will build and tag it with a generated name, and use that image thereafter.


### dockerfile

Alternate Dockerfile.

Compose will use an alternate file to build with.

    dockerfile: Dockerfile-alternate

### command

Override the default command.

    command: bundle exec thin -p 3000

<a name="links"></a>
### links

Link to containers in another service. Either specify both the service name and
the link alias (`SERVICE:ALIAS`), or just the service name (which will also be
used for the alias).

    links:
     - db
     - db:database
     - redis

An entry with the alias' name will be created in `/etc/hosts` inside containers
for this service, e.g:

    172.17.2.186  db
    172.17.2.186  database
    172.17.2.187  redis

Environment variables will also be created - see the [environment variable
reference](env.md) for details.

### external_links

Link to containers started outside this `docker-compose.yml` or even outside
of Compose, especially for containers that provide shared or common services.
`external_links` follow semantics similar to `links` when specifying both the
container name and the link alias (`CONTAINER:ALIAS`).

    external_links:
     - redis_1
     - project_db_1:mysql
     - project_db_1:postgresql

### extra_hosts

Add hostname mappings. Use the same values as the docker client `--add-host` parameter.

    extra_hosts:
     - "somehost:162.242.195.82"
     - "otherhost:50.31.209.229"

An entry with the ip address and hostname will be created in `/etc/hosts` inside containers for this service, e.g:

    162.242.195.82  somehost
    50.31.209.229   otherhost

### ports

Makes an exposed port accessible on a host and the port is available to
any client that can reach that host. Docker binds the exposed port to a random
port on the host within an *ephemeral port range* defined by
`/proc/sys/net/ipv4/ip_local_port_range`. You can also map to a specific port or range of ports.

Acceptable formats for the `ports` value are:

* `containerPort`
* `ip:hostPort:containerPort`
* `ip::containerPort`
* `hostPort:containerPort`

You can specify a range for both the `hostPort` and the `containerPort` values.
When specifying ranges, the container port values in the range must match the
number of host port values in the range, for example,
`1234-1236:1234-1236/tcp`. Once a host is running, use the 'docker-compose port' command
to see the actual mapping.

The following configuration shows examples of the port formats in use:

    ports:
     - "3000"
     - "3000-3005"
     - "8000:8000"
     - "9090-9091:8080-8081"
     - "49100:22"
     - "127.0.0.1:8001:8001"
     - "127.0.0.1:5000-5010:5000-5010"


When mapping ports, in the `hostPort:containerPort` format, you may
experience erroneous results when using a container port lower than 60. This
happens because YAML parses numbers in the format `xx:yy` as sexagesimal (base
60). To avoid this problem, always explicitly specify your port
mappings as strings.

### expose

Expose ports without publishing them to the host machine - they'll only be
accessible to linked services. Only the internal port can be specified.

    expose:
     - "3000"
     - "8000"

### volumes

Mount paths as volumes, optionally specifying a path on the host machine
(`HOST:CONTAINER`), or an access mode (`HOST:CONTAINER:ro`).

    volumes:
     - /var/lib/mysql
     - ./cache:/tmp/cache
     - ~/configs:/etc/configs/:ro

You can mount a relative path on the host, which will expand relative to
the directory of the Compose configuration file being used. Relative paths
should always begin with `.` or `..`.

> Note: No path expansion will be done if you have also specified a
> `volume_driver`.

### volumes_from

Mount all of the volumes from another service or container.

    volumes_from:
     - service_name
     - container_name

### environment

Add environment variables. You can use either an array or a dictionary.

Environment variables with only a key are resolved to their values on the
machine Compose is running on, which can be helpful for secret or host-specific values.

    environment:
      RACK_ENV: development
      SESSION_SECRET:

    environment:
      - RACK_ENV=development
      - SESSION_SECRET

### env_file

Add environment variables from a file. Can be a single value or a list.

If you have specified a Compose file with `docker-compose -f FILE`, paths in
`env_file` are relative to the directory that file is in.

Environment variables specified in `environment` override these values.

    env_file: .env

    env_file:
      - ./common.env
      - ./apps/web.env
      - /opt/secrets.env

Compose expects each line in an env file to be in `VAR=VAL` format. Lines
beginning with `#` (i.e. comments) are ignored, as are blank lines.

    # Set Rails/Rack environment
    RACK_ENV=development

### extends

Extend another service, in the current file or another, optionally overriding
configuration.

Here's a simple example. Suppose we have 2 files - **common.yml** and
**development.yml**. We can use `extends` to define a service in
**development.yml** which uses configuration defined in **common.yml**:

**common.yml**

    webapp:
      build: ./webapp
      environment:
        - DEBUG=false
        - SEND_EMAILS=false

**development.yml**

    web:
      extends:
        file: common.yml
        service: webapp
      ports:
        - "8000:8000"
      links:
        - db
      environment:
        - DEBUG=true
    db:
      image: postgres

Here, the `web` service in **development.yml** inherits the configuration of
the `webapp` service in **common.yml** - the `build` and `environment` keys -
and adds `ports` and `links` configuration. It overrides one of the defined
environment variables (DEBUG) with a new value, and the other one
(SEND_EMAILS) is left untouched.

The `file` key is optional, if it is not set then Compose will look for the
service within the current file.

For more on `extends`, see the [tutorial](extends.md#example) and
[reference](extends.md#reference).

### labels

Add metadata to containers using [Docker labels](http://docs.docker.com/userguide/labels-custom-metadata/). You can use either an array or a dictionary.

It's recommended that you use reverse-DNS notation to prevent your labels from conflicting with those used by other software.

    labels:
      com.example.description: "Accounting webapp"
      com.example.department: "Finance"
      com.example.label-with-empty-value: ""

    labels:
      - "com.example.description=Accounting webapp"
      - "com.example.department=Finance"
      - "com.example.label-with-empty-value"

### container_name

Specify a custom container name, rather than a generated default name.

    container_name: my-web-container

Because Docker container names must be unique, you cannot scale a service
beyond 1 container if you have specified a custom name. Attempting to do so
results in an error.

### log driver

Specify a logging driver for the service's containers, as with the ``--log-driver`` option for docker run ([documented here](http://docs.docker.com/reference/run/#logging-drivers-log-driver)).

Allowed values are currently ``json-file``, ``syslog`` and ``none``. The list will change over time as more drivers are added to the Docker engine.

The default value is json-file.

    log_driver: "json-file"
    log_driver: "syslog"
    log_driver: "none"

Specify logging options with `log_opt` for the logging driver, as with the ``--log-opt`` option for `docker run`.

Logging options are key value pairs. An example of `syslog` options:

    log_driver: "syslog"
    log_opt:
      syslog-address: "tcp://192.168.0.42:123"

### net

Networking mode. Use the same values as the docker client `--net` parameter.

    net: "bridge"
    net: "none"
    net: "container:[name or id]"
    net: "host"

### pid

    pid: "host"

Sets the PID mode to the host PID mode.  This turns on sharing between
container and the host operating system the PID address space.  Containers
launched with this flag will be able to access and manipulate other
containers in the bare-metal machine's namespace and vise-versa.

### dns

Custom DNS servers. Can be a single value or a list.

    dns: 8.8.8.8
    dns:
      - 8.8.8.8
      - 9.9.9.9

### cap_add, cap_drop

Add or drop container capabilities.
See `man 7 capabilities` for a full list.

    cap_add:
      - ALL

    cap_drop:
      - NET_ADMIN
      - SYS_ADMIN

### dns_search

Custom DNS search domains. Can be a single value or a list.

    dns_search: example.com
    dns_search:
      - dc1.example.com
      - dc2.example.com

### devices

List of device mappings.  Uses the same format as the `--device` docker
client create option.

    devices:
      - "/dev/ttyUSB0:/dev/ttyUSB0"

### security_opt

Override the default labeling scheme for each container.

      security_opt:
        - label:user:USER
        - label:role:ROLE

### working\_dir, entrypoint, user, hostname, domainname, mac\_address, mem\_limit, memswap\_limit, privileged, restart, stdin\_open, tty, cpu\_shares, cpuset, read\_only, volume\_driver

Each of these is a single value, analogous to its
[docker run](https://docs.docker.com/reference/run/) counterpart.

    cpu_shares: 73
    cpuset: 0,1

    working_dir: /code
    entrypoint: /code/entrypoint.sh
    user: postgresql

    hostname: foo
    domainname: foo.com

    mac_address: 02:42:ac:11:65:43

    mem_limit: 1000000000
    memswap_limit: 2000000000
    privileged: true

    restart: always

    stdin_open: true
    tty: true
    read_only: true

    volume_driver: mydriver

## Variable substitution

Your configuration options can contain environment variables. Compose uses the
variable values from the shell environment in which `docker-compose` is run. For
example, suppose the shell contains `POSTGRES_VERSION=9.3` and you supply this
configuration:

    db:
      image: "postgres:${POSTGRES_VERSION}"

When you run `docker-compose up` with this configuration, Compose looks for the
`POSTGRES_VERSION` environment variable in the shell and substitutes its value
in. For this example, Compose resolves the `image` to `postgres:9.3` before
running the configuration.

If an environment variable is not set, Compose substitutes with an empty
string. In the example above, if `POSTGRES_VERSION` is not set, the value for
the `image` option is `postgres:`.

Both `$VARIABLE` and `${VARIABLE}` syntax are supported. Extended shell-style
features, such as `${VARIABLE-default}` and `${VARIABLE/foo/bar}`, are not
supported.

If you need to put a literal dollar sign in a configuration value, use a double
dollar sign (`$$`).


## Compose documentation

- [User guide](/)
- [Installing Compose](install.md)
- [Get started with Django](django.md)
- [Get started with Rails](rails.md)
- [Get started with Wordpress](wordpress.md)
- [Command line reference](/reference)
- [Compose environment variables](env.md)
- [Compose command line completion](completion.md)
