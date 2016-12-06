#!/usr/bin/env python
 
import sys
import qarnot
 
# Edit 'samples.conf' to provide your own credentials
 
# Create a connection, from which all other objects will be derived
conn = qarnot.Connection('samples.conf')
 
# Create a task. The 'with' statement ensures that the task will be
# deleted in the end, to prevent tasks from continuing to run after
# a Ctrl-C for instance
task = conn.create_task('sample1-helloword-advanced', 'docker-batch', 2)

# Store if an error happened during the process
error_happened = False
try:
    # Set the command to run when launching the container, by overriding a
    # constant.
    # Task constants are the main way of controlling a task's behaviour
    task.constants['DOCKER_CMD'] = 'sh -c "echo Hello world from $QRANK/$QSIZE!"'
 
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
 
    # Display errors on failure
    if task.state == 'Failure':
        print("** Errors: %s" % task.errors[0])
        error_happened = True


finally:
    task.delete(purge_resources=True, purge_results=True)
    # Exit code in case of error
    if error_happened:
        sys.exit(1)
