TODO
====

Pay attention to the language
-----------------------------

While the install step may be used to install requisite packages, it is more
convenient and flexible if we take a hint from the 'language' config and
install the appropriate environment for that language.  This also allows the
builder to be executed outside of a container in a plain old development
environment without the user having to selectively suppress install steps
through environment variables.

To support each language, there needs to be additional toolchain images built
on top of the base image.  On start, the container corresponding with the
language must be used as a base for the final container.

golang:

    apt-get install -qy golang golang-go.tools

ruby (rvm only):

    curl -sSL https://get.rvm.io | bash -s stable
    (install the ruby version requested in the config)
    gem install bundler rake

nodejs:

    apt-get install -qy nodejs npm

python:

    apt-get install -qy python python-dev
    pip install nose pytest mock wheel

python3:

    apt-get install -qy python3 python3-dev
    pip3 install nose pytest mock wheel
