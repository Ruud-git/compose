Docker Compose
==============
[![Build Status](https://ci-next.docker.com/public/buildStatus/icon?job=compose/master)](https://ci-next.docker.com/public/job/compose/job/master/)

![Docker Compose](logo.png?raw=true "Docker Compose Logo")

# :warning: *Compose V1 is DEPRECATED* :warning:
Since [Compose V2 is now GA](https://www.docker.com/blog/announcing-compose-v2-general-availability/), Compose V1 is officially **End of Life**. This means that:
- Active development and new features will only be added to the V2 codebase
- Only security-related issues will be considered for V1

Check out the [V2 branch here](https://github.com/docker/compose/tree/v2/)!!

---------------------------------------------

** Compose V2 is **Generally Available**! :star_struck: **
---------------------------------------------

Check it out [here](https://github.com/docker/compose/tree/v2/)!

Read more on the [GA announcement here](https://www.docker.com/blog/announcing-compose-v2-general-availability/)

---------------------------------------------

V1 vs V2 transition :hourglass_flowing_sand:
--------------------------------------------

"Generally Available" will mean:
- New features and bug fixes will only be considered in the V2 codebase 
- Users on Mac/Windows will be defaulted into Docker Compose V2, but can still opt out through the UI and the CLI. This means when running `docker-compose` you will actually be running `docker compose`
- Our current goal is for users on Linux to receive Compose v2 with the latest version of the docker CLI, but is pending some technical discussion. Users will be able to use [compose switch](https://github.com/docker/compose-switch) to enable redirection of `docker-compose` to `docker compose`
- Docker Compose V1 will continue to be maintained regarding security issues
- [v2 branch](https://github.com/docker/compose/tree/v2) will become the default one at that time

:lock_with_ink_pen: Depending on the feedback we receive from the community of GA and the adoption on Linux, we will come up with a plan to deprecate v1, but as of right now there is no concrete timeline as we want the transition to be as smooth as possible for all users. It is important to note that we have no plans of removing any aliasing of `docker-compose` to `docker compose`. We want to make it as easy as possible to switch and not break any ones scripts. We will follow up with a blog post in the next few months with more information of an exact timeline of V1 being marked as deprecated and end of support for security issues. We’d love to hear your feedback! You can provide it [here](https://github.com/docker/roadmap/issues/257).

About
-----

Docker Compose is a tool for running multi-container applications on Docker
defined using the [Compose file format](https://compose-spec.io).
A Compose file is used to define how the one or more containers that make up
your application are configured.
Once you have a Compose file, you can create and start your application with a
single command: `docker-compose up`.

Compose files can be used to deploy applications locally, or to the cloud on
[Amazon ECS](https://aws.amazon.com/ecs) or
[Microsoft ACI](https://azure.microsoft.com/services/container-instances/) using
the Docker CLI. You can read more about how to do this:
- [Compose for Amazon ECS](https://docs.docker.com/engine/context/ecs-integration/)
- [Compose for Microsoft ACI](https://docs.docker.com/engine/context/aci-integration/)

Where to get Docker Compose
----------------------------

All the instructions to install the Python version of Docker Compose, aka `v1`, 
are described in the [installation guide](./INSTALL.md). 

> ⚠️ This version is a deprecated version of Compose. We recommend that you use the [latest version of Docker Compose](https://docs.docker.com/compose/install/).

Quick Start
-----------

Using Docker Compose is basically a three-step process:
1. Define your app's environment with a `Dockerfile` so it can be
   reproduced anywhere.
2. Define the services that make up your app in `docker-compose.yml` so
   they can be run together in an isolated environment.
3. Lastly, run `docker-compose up` and Compose will start and run your entire
   app.

A Compose file looks like this:

```yaml
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - .:/code
  redis:
    image: redis
```

You can find examples of Compose applications in our
[Awesome Compose repository](https://github.com/docker/awesome-compose).

For more information about the Compose format, see the
[Compose file reference](https://docs.docker.com/compose/compose-file/).

Contributing
------------

Want to help develop Docker Compose? Check out our
[contributing documentation](https://github.com/docker/compose/blob/master/CONTRIBUTING.md).

If you find an issue, please report it on the
[issue tracker](https://github.com/docker/compose/issues/new/choose).

Releasing
---------

Releases are built by maintainers, following an outline of the [release process](https://github.com/docker/compose/blob/master/project/RELEASE-PROCESS.md).
