conn = qarnot.Connection('qarnot.conf')
# [...]
DOCKER_REPO = 'qarnotlab/pymor_fenics'
DOCKER_TAG = '2020.2.0_2019.1.0'

TRAIN_PARAM_NB = 120  # Number of parameter value for training
TRAIN_INST = 30  # Number of instance that will compute in parrallel
# [...]
input_bucket = conn.create_bucket('input')
input_bucket.sync_directory('input')  # adding the content of directory ./input into ressource bucket
fom_res_bucket = conn.create_bucket('fom-results')
# [...]
train_task = conn.create_task('train', 'docker-batch', TRAIN_INST, job=job)
train_task.constants['DOCKER_REPO'] = DOCKER_REPO
train_task.constants['DOCKER_TAG'] = DOCKER_TAG
# h5repack compresse the solution files to quicken data exchanges
train_task.constants['DOCKER_CMD'] = f"'python3 main.py -n {TRAIN_PARAM_NB} -o train/u &&" + \
                                "h5repack -f GZIP=1 train/u${INSTANCE_ID}.h5 train/u${INSTANCE_ID}_c.h5'"
train_task.resources.append(input_bucket)
train_task.results = fom_res_bucket
train_task.results_whitelist = r'_c.h5'  # we only want to withdraw compressed files
# [...]
train_task.submit()