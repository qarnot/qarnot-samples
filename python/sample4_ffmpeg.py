#!/usr/bin/env python
 
import sys
import qarnot

# Parse ffmpeg command line

# Check if some arguments were provided
args = sys.argv[1:]
if len(args) == 0:
    sys.stderr.write("usage: %s [ffmpeg arguments]\n" % sys.argv[0])
    sys.exit(1)

# Build the full command line
ffmpeg_cmd = ' '.join(args)

# Find the input file
input_file = None
for i in xrange(0, len(args)-1):
  if args[i] == "-i": input_file = args[i+1]

# Display that we parsed
print("** FFMPEG command: %s" % ffmpeg_cmd)
print("** Input file: %s" % input_file)
 
# Edit 'samples.conf' to provide your own credentials
 
# Create a connection, from which all other objects will be derived
conn = qarnot.Connection('samples.conf')

# Create a task. The 'with' statement ensures that the task will be
# deleted in the end, to prevent tasks from continuing to run after
# a Ctrl-C for instance
task = conn.create_task('sample4-ffmpeg', 'docker-batch', 1)
try:
    # Set the command to run when launching the container, by overriding a
    # constant.
    # Task constants are the main way of controlling a task's behaviour
    task.constants['DOCKER_REPO'] = 'jrottenberg/ffmpeg'
    task.constants['DOCKER_CMD'] = ffmpeg_cmd
    #task.constants['DOCKER_CMD'] = "sleep 3600"

    if input_file != None:
        # Create a resource disk and add our input file.
        input_disk = conn.create_disk('sample4-ffmpeg-input-resource')
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
    else: 
        # Or downlaod the results
        task.download_results('.')

finally:
    task.delete()
    pass

