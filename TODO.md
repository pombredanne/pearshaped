TODO
====

 - clean up intermediate containers upon a successful build
 - correctly support building multiple repos
 - record build information and store metadata
   - start/end timestamps
   - success
   - git hash
   - build number
 - listen for github commit hooks
 - allow the user to configure repos and branches to watch
 - support ouputting to a build monitor such as https://github.com/pivotal/projectmonitor

Pay attention to the language
-----------------------------

While the install step may be used to install requisite packages, it is more
convenient and flexible if we take a hint from the 'language' variable and
install the appropriate environment for that language.  

The language variable allows the build to be executed outside of a container in
a plain old development environment without the user having to selectively
suppress toolchain installation steps.

Currently, the language must exactly match an image name. We should add
support for several common toolchains.


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

Support toolchain matrices
--------------------------

Provide multiple popular versions of each language toolchain and allow
a build to run against more than one of them.
