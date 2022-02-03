from datetime import datetime
import qarnot
from time import sleep

def wait_loop(task_list):
    '''Wait loop that wait for every tasks in task_list to be finished'''
    finished = [False for t in task_list]
    while finished.count(True) < len(finished):
        for i, t in enumerate(task_list):
            if not finished[i] and t.wait(0.1):
                finished[i] = True
                print(f'task {t.name} finished with state {t.state}.  {finished.count(True)}/{len(finished)}')
                if t.state != 'Success':
                    raise RuntimeError(f'task {t.name} failed: {t.errors}.\n' + 
                                       'See https://console.qarnot.com/app/tasks for more info')
        sleep(1)
    pass


if __name__=='__main__':
    conn = qarnot.Connection('qarnot.conf')
    job = conn.create_job('rom-job', useDependencies=True)
    job.submit()
    
    DOCKER_REPO = 'qarnotlab/pymor_fenics'
    DOCKER_TAG = '2020.2.0_2019.1.0'
    
    TRAIN_PARAM_NB = 120
    TRAIN_INST = 30
    VAL_PARAM_NB = 50
    VAL_INST = 25
    RB_SIZE = 50
    
    input_bucket = conn.create_bucket('input')
    input_bucket.sync_directory('input')
    fom_res_bucket = conn.create_bucket('fom-results')
    rom_bucket = conn.create_bucket('rom')
    rom_res_bucket = conn.create_bucket('rom-results')
    param_bucket = conn.create_bucket('param')
    rom_compare_bucket = conn.create_bucket('compare')

    train_task = conn.create_task('train', 'docker-batch', TRAIN_INST, job=job)
    train_task.constants['DOCKER_REPO'] = DOCKER_REPO
    train_task.constants['DOCKER_TAG'] = DOCKER_TAG
    # h5repack compresse the solution files to quicken data exchanges
    train_task.constants['DOCKER_CMD'] = f"'python3 main.py -n {TRAIN_PARAM_NB} -o train/u &&" + \
                                    "h5repack -f GZIP=1 train/u${INSTANCE_ID}.h5 train/u${INSTANCE_ID}_c.h5'"
    train_task.resources.append(input_bucket)
    train_task.results = fom_res_bucket
    train_task.results_whitelist = r'_c.h5'
    
    rom_task = conn.create_task('rom-build', 'docker-batch', 1, job=job)
    rom_task.constants['DOCKER_REPO'] = DOCKER_REPO
    rom_task.constants['DOCKER_TAG'] = DOCKER_TAG
    rom_task.constants['DOCKER_CMD'] = f"'python3 rombuild.py -n {TRAIN_INST} -m {RB_SIZE} -i train'"
    rom_task.resources.append(fom_res_bucket)
    rom_task.resources.append(input_bucket)
    rom_task.results = rom_bucket
    
    write_param_task = conn.create_task('write-param', 'docker-batch', 1, job=job)
    write_param_task.constants['DOCKER_REPO'] = DOCKER_REPO
    write_param_task.constants['DOCKER_TAG'] = DOCKER_TAG
    write_param_task.constants['DOCKER_CMD'] = f"'python3 writeparam.py {VAL_PARAM_NB}'"
    write_param_task.resources.append(input_bucket)
    write_param_task.results = param_bucket
    
    fom_val_task = conn.create_task('fom-val', 'docker-batch', VAL_INST, job=job)
    fom_val_task.constants['DOCKER_REPO'] = DOCKER_REPO
    fom_val_task.constants['DOCKER_TAG'] = DOCKER_TAG
    fom_val_task.constants['DOCKER_CMD'] = "'python3 main.py -i param.pkl -o val/u &&" + \
                                    "h5repack -f GZIP=1 val/u${INSTANCE_ID}.h5 val/u${INSTANCE_ID}_c.h5'"
    fom_val_task.resources.append(input_bucket)
    fom_val_task.resources.append(param_bucket)
    fom_val_task.results = fom_res_bucket
    fom_val_task.results_whitelist = r'_c.h5'
    
    rom_val_task = conn.create_task('rom-val', 'docker-batch', 1, job=job)
    rom_val_task.constants['DOCKER_REPO'] = DOCKER_REPO
    rom_val_task.constants['DOCKER_TAG'] = DOCKER_TAG
    rom_val_task.constants['DOCKER_CMD'] = "'python3 romsolve.py -i param.pkl'"
    rom_val_task.resources.append(input_bucket)
    rom_val_task.resources.append(rom_bucket)
    rom_val_task.resources.append(param_bucket)
    rom_val_task.results = rom_res_bucket
    
    rom_compare_task = conn.create_task('rom-compare', 'docker-batch', 1, job=job)
    rom_compare_task.constants['DOCKER_REPO'] = DOCKER_REPO
    rom_compare_task.constants['DOCKER_TAG'] = DOCKER_TAG
    rom_compare_task.constants['DOCKER_CMD'] = "'python3 romcompare.py -i val'"
    rom_compare_task.resources.append(input_bucket)
    rom_compare_task.resources.append(rom_bucket)
    rom_compare_task.resources.append(rom_res_bucket)
    rom_compare_task.resources.append(fom_res_bucket)
    rom_compare_task.results = rom_compare_bucket
    
    train_task.submit()
    write_param_task.submit()
    rom_task.set_task_dependencies_from_tasks([train_task])
    rom_task.submit()
    fom_val_task.set_task_dependencies_from_tasks([write_param_task])
    fom_val_task.submit()
    rom_val_task.set_task_dependencies_from_tasks([write_param_task, rom_task])
    rom_val_task.submit()
    rom_compare_task.set_task_dependencies_from_tasks([rom_val_task, fom_val_task])
    rom_compare_task.submit()

    print('waiting for tasks to finish...')
    wait_loop([train_task, write_param_task, rom_task, fom_val_task, rom_val_task, rom_compare_task])
    
    print('\n\n********  Time results ********')
    print(f'Training time: {train_task.execution_time}. Done in {train_task.wall_time} thanks to parallelization')
    print(f'ROM building time: {rom_task.execution_time}')
    print(f'FOM compute time for validation set: {fom_val_task.execution_time}')
    print(f'ROM compute time for validation set: {rom_val_task.execution_time}')
    rom_sec = datetime.strptime(rom_val_task.execution_time, "%H:%M:%S")
    rom_sec = (rom_sec - datetime(1900, 1, 1)).seconds
    fom_sec = datetime.strptime(fom_val_task.execution_time, "%H:%M:%S")
    fom_sec = (fom_sec - datetime(1900, 1, 1)).seconds
    print(f'ROM is {fom_sec//rom_sec} times quicker')

    print('\n\n********  ROM precision ********')
    print('see output of task rom-compare in console: https://console.qarnot.com/app/tasks')
    print('bucket compare contains graph of errors')
