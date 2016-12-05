#!/usr/bin/env python

import qarnot
import os
import sys

input_file = 'blender/qarnot.blend'

# Edit 'samples.conf' to provide your own credentials

# Create a connection, from which all other objects will be derived
conn = qarnot.Connection('samples.conf')

# Create a task.
# Because we are selecting the frame to render inside the task, put the framecount to 0
task = conn.create_task('sample5-blender', 'blender', 0)

# Store if an error happened during the process
error_happened = False
try:
    # Create a resource disk and add an input file
    print("** Uploading %s..." % input_file)
    input_disk = conn.create_disk('sample5-blender-input-resource')
    input_disk.add_file(input_file)

    # Attach the disk to the task
    task.resources.append(input_disk)

    # Render the frame 115 to 120
    task.advanced_range = '115-120'

    # Task constants are the main way of controlling a task's behaviour
    task.constants['BLEND_FILE'] = os.path.basename(input_file)
    task.constants['BLEND_SLICING'] = '1'
    task.constants['BLEND_ENGINE'] = 'CYCLES'
    task.constants['BLEND_FORMAT'] = 'PNG'
    task.constants['BLEND_W'] = '1920'
    task.constants['BLEND_H'] = '1080'
    task.constants['BLEND_RATIO'] = '50'  # Limit ratio for testing purposes
    task.constants['BLEND_CYCLES_SAMPLES'] = '20'

    # Submit the task to the Api, that will launch it on the cluster
    task.submit()

    # Wait for the task to be finished, and monitor its progress
    last_state = ''
    last_execution_progress = 0.0
    done = False    
    while not done:
        if task.status is not None and task.status.execution_progress != last_execution_progress:
            last_execution_progress = task.status.execution_progress
            print("** Overall progress {}%".format(last_execution_progress))

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

    # Download succeeded frames
    task.download_results('output')

finally:
    task.delete(purge_resources=True, purge_results=True)
    # Exit code in case of error
    if error_happened:
        sys.exit(1)
    pass
