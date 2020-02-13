#!/usr/bin/env python

# Import the Qarnot sdk
import qarnot

# Connection to the Qarnot platform
conn=qarnot.Connection(client_token='  --- Your token here  --- ')

# Creation of the task
task = conn.create_task("Ascendance", "docker-batch", 1)

# Creation of an input bucket and synchronization with a local file
bucket = conn.create_bucket("input")
bucket.sync_directory("UseCaseAscendance")

# Creation of an output bucket and synchronization with the task
output_bucket = conn.create_bucket("output")
task.results = output_bucket
task.resources = [ bucket ]

# Docker image and command to be run in he container
task.constants["DOCKER_REPO"] = "docker/image"
task.constants["DOCKER_TAG"] = "default_latest"
task.constants["DOCKER_CMD"] = "/job/run"

# Task submission
task.submit()
