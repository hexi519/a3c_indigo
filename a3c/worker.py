#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
import argparse
import project_root
import numpy as np
import tensorflow as tf
from subprocess import check_call
from os import path
from a3c import A3C
from env.environment import Environment
import os
os.environ["CUDA_VISIBLE_DEVICES"]="-1"

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# 调用generate_trace --> 整数可以直接生成
def prepare_traces(bandwidth):
    trace_dir = path.join(project_root.DIR, 'env')

    if type(bandwidth) == int:
        if bandwidth != 12:  # 目前只有12Mbps的
            gen_trace = path.join(project_root.DIR, 'helpers',
                                  'generate_trace.py')
            cmd = [
                'python', gen_trace, '--output-dir', trace_dir, '--bandwidth',
                str(bandwidth)
            ]
            # sys.stderr.write('$ %s\n' % ' '.join(cmd))
            check_call(cmd)

        uplink_trace = path.join(trace_dir, '%dmbps_jitter.trace' % bandwidth)
        downlink_trace = uplink_trace
    else:
        trace_path = path.join(trace_dir, bandwidth)  # 非整数的就没法generate的了
        # intentionally switch uplink and downlink traces due to sender first
        uplink_trace = trace_path + '.down'
        downlink_trace = trace_path + '.up'

    return uplink_trace, downlink_trace


def create_env(task_index):
    bandwidth_list = [100, 200]
    delay_list = [5, 10, 20]
    # queue = [100,200,400]
    # loss = [0.0001,0.001,0.01]
    loss_list = [0.1, 0.001]

    cartesian = [(b, d, k) for b in bandwidth_list for d in delay_list
                 for k in loss_list]
    bandwidth, delay, loss = cartesian[task_index]

    # sys.stderr.write('\nhesy debug: env len is %d\n' % len(cartesian))

    uplink_trace, downlink_trace = prepare_traces(bandwidth)
    mm_cmd = 'mm-delay %d mm-loss uplink %f mm-link %s %s' % (
        delay, loss, uplink_trace, downlink_trace)
    """
    bandwidth = int(np.linspace(30, 60, num=4, dtype=np.int)[task_index]) 
    delay = 25
    queue = None

    uplink_trace, downlink_trace = prepare_traces(bandwidth)
    mm_cmd = ('mm-delay %d mm-link %s %s' %
              (delay, uplink_trace, downlink_trace))
    if queue is not None:
        mm_cmd += (' --downlink-queue=droptail '
                   '--downlink-queue-args=packets=%d' % queue)
    """
    env = Environment(mm_cmd)
    #env.setup()
    return env


# 似乎不需要
def shutdown_from_driver(driver):
    cmd = ['ssh', driver, '~/RLCC/helpers/shutdown.sh']
    check_call(cmd)


def run(args):
    job_name = args.job_name
    task_index = args.task_index
    # sys.stderr.write('Starting job %s task %d\n' % (job_name, task_index))

    ps_hosts = args.ps_hosts.split(',')
    worker_hosts = args.worker_hosts.split(',')

    cluster = tf.train.ClusterSpec({'ps': ps_hosts, 'worker': worker_hosts})
    server = tf.train.Server(cluster, job_name=job_name, task_index=task_index)

    if job_name == 'ps':
        server.join()
    elif job_name == 'worker':
        env = create_env(task_index)

        ## 回头这里可以把GPU的参数传进去
        learner = A3C(
            cluster=cluster,
            server=server,  # create session的时候要用
            task_index=task_index,
            env=env,
            dagger=args.dagger)

        try:
            learner.run()
        except KeyboardInterrupt:
            pass
        finally:
            learner.cleanup()
            if args.driver is not None:
                shutdown_from_driver(args.driver)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--ps-hosts',
        required=True,
        metavar='[HOSTNAME:PORT, ...]',
        help='comma-separated list of hostname:port of parameter servers')
    parser.add_argument(
        '--worker-hosts',
        required=True,
        metavar='[HOSTNAME:PORT, ...]',
        help='comma-separated list of hostname:port of workers')
    parser.add_argument('--job-name',
                        choices=['ps', 'worker'],
                        required=True,
                        help='ps or worker')
    parser.add_argument('--task-index',
                        metavar='N',
                        type=int,
                        required=True,
                        help='index of task')
    parser.add_argument('--dagger',
                        action='store_true',
                        help='run Dagger rather than A3C')
    parser.add_argument('--driver', help='hostname of the driver')
    args = parser.parse_args()

    # run parameter servers and workers
    run(args)


if __name__ == '__main__':
    main()
