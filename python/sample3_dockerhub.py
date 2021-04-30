#!/usr/bin/env python

import sys
import qarnot
import os
import operator

# Edit 'samples.conf' to provide your own credentials

# Create a connection, from which all other objects will be derived
conn = qarnot.Connection('samples.conf')

# A set of linux distributions that could be found on https://hub.docker.com/explore/
# Each distribution is started in a different task. All the tasks are running in parallel
linux_versions = ["library/centos:5",      \
                  "library/centos:6",      \
                  "library/ubuntu:14.04",  \
                  "library/ubuntu:16.04",  \
                  "library/debian:jessie", \
                  "opensuse/leap:42.3", \
                  "archlinux:latest"]

# Create the tasks
tasks = {i: conn.create_task('sample3-dockerhub-%s' % i, 'docker-batch', 1) for i in linux_versions}

# Store if an error happened during the process
error_happened = False
try:
    # Set the command to run when launching the container, by overriding a
    # constant.
    # Task constants are the main way of controlling a task's behaviour
    for version,task in tasks.items():
        (repo,tag) = version.split(':')
        task.constants['DOCKER_REPO'] = repo
        task.constants['DOCKER_TAG'] = tag
        task.constants['DOCKER_CMD'] = 'sh -c "cat /etc/issue | head -n 1"'
        print("** Submitting %s..." % task.name)

        # Submit the task to the Api, that will launch it on the cluster
        task.submit()

    # Wait for the task to be finished, and monitor the progress of its
    # deployment
    last_state = {task.name: '' for task in tasks.values()}
    done = False
    while not done:
        for task in tasks.values():
            if task.state != last_state[task.name]:
                last_state[task.name] = task.state
                print("** {} >>> {}".format(task.name, last_state[task.name]))

        # Wait for the task to complete, with a timeout of 2 seconds.
        # This will return True as soon as the task is complete, or False
        # after the timeout.
        done = all([task.wait(2) for task in tasks.values()])

        # Display fresh stdout / stderr
        map(sys.stdout.write, [task.fresh_stdout() for task in tasks.values()])
        map(sys.stderr.write, [task.fresh_stderr() for task in tasks.values()])

    # Display errors on failure
    for task in tasks.values():
        if task.state == 'Failure':
            print("** %s >>> Errors: %s" % (task.name, task.errors[0]))
            error_happened = True


finally:
    for task in tasks.values():
        task.delete(purge_resources=True, purge_results=True)

    # Exit code in case of error
    if error_happened:
        sys.exit(1)
