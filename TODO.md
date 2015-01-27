TODO
====

 - clean up intermediate containers and images upon a successful build
 - record build information and store metadata
   - start/end timestamps
   - success
   - git hash
   - build number
 - make ctrl-c work well (e.g. clean up running containers)
 - build images at dockerhub on each commit
 - listen for github commit hooks
 - allow the user to configure repos and branches to watch
 - allow jobs to be cancelled and cleaned up
 - if the install step does not change, resume from saved container
 - support outputting to a build monitor such as https://github.com/pivotal/projectmonitor
 - let the user store containers for failed builds with a deletion policy
   - by default, only store the very last build for a project
 - provide a tool for resuming a build from a previous state with the latest repo version
 - allow builds to produce and save artifacts
 - build matrices across multiple dimensions (e.g. branch, env, and toolchain version)

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


Support toolchain matrices
--------------------------

Provide multiple popular versions of each language toolchain and allow
a build to run against more than one of them.
