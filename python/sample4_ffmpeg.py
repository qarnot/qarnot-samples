#!/usr/bin/env python
import argparse
import sys
import qarnot

# Parse ffmpeg command line

# Create a argument parser to parse input files
parser = argparse.ArgumentParser()
parser.add_argument('-i', action='append', required=True)

# Get arguments
args = sys.argv[1:]

# Parse input files and store them as a list
input_files = parser.parse_known_args(args)[0].i

# Build the full command line
ffmpeg_cmd = ' '.join(args)

# Display that we parsed
print("** FFMPEG command: %s" % ffmpeg_cmd)
print("** Input files: %s" % ', '.join(input_files))

# Edit 'samples.conf' to provide your own credentials

# Create a connection, from which all other objects will be derived
conn = qarnot.Connection('samples.conf')

# Create a task with the batch profile.
task = conn.create_task('sample4-ffmpeg', 'docker-batch', 1)

# Store if an error happened during the process
error_happened = False

try:
    # Set the command to run when launching the container, by overriding a
    # constant.
    # Task constants are the main way of controlling a task's behaviour
    task.constants['DOCKER_REPO'] = 'jrottenberg/ffmpeg'
    task.constants['DOCKER_TAG'] = 'ubuntu'
    task.constants['DOCKER_CMD'] = ffmpeg_cmd
    # task.constants['DOCKER_CMD'] = "sleep 3600"

    input_disk = conn.create_disk('sample4-ffmpeg-input-resource')
    for input_file in input_files:
        # Create a resource disk and add our input file.
        input_disk[input_file] = input_file

    # Attach the disk to the task
    task.resources.append(input_disk)

    # Submit the task to the Api, that will launch it on the cluster
    task.submit()

    # Wait for the task to be finished, and monitor the progress of its
    # deployment
    last_state = ''
    done = False
    while not done:
        if task.state != last_state:
            last_state = task.state
            print("** {}".format(last_state))

        # Wait for the task to complete, with a timeout of 5 seconds.
        # This will return True as soon as the task is complete, or False
        # after the timeout.
        done = task.wait(5)

        # Display fresh stdout / stderr
        sys.stdout.write(task.fresh_stdout())
        sys.stderr.write(task.fresh_stderr())

    if task.state == 'Failure':
        # Display errors on failure
        print("** Errors: %s" % task.errors[0])
        error_happened = True
    else:
        # Or download the results
        task.download_results('.')

finally:
    task.delete(purge_resources=True, purge_results=True)
    # Exit code in case of error
    if error_happened:
        sys.exit(1)
