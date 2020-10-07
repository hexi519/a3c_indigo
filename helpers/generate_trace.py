#!/usr/bin/env python

# Copyright 2018 Francis Y. Yan, Jestin Ma
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import argparse
import numpy as np
from os import path
from helpers import make_sure_path_exists


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bandwidth', metavar='Mbps', required=True,
                        help='constant bandwidth (Mbps)')
    parser.add_argument('--output-dir',default="/home/hesy/pro/pan/pantheon/src/experiments", metavar='DIR',
                        help='directory to output trace')
    args = parser.parse_args()

    """
    # number of packets in 60 seconds
    num_packets = int(float(args.bandwidth) * 5000) 
    ts_list = np.linspace(0, 60000, num=num_packets, endpoint=False)
    """
    # number of packets in 48 seconds
    # change each 12s ( 4 periods )        -- which produces a integer
    duration = 12*1000
    begin,end = 0,0+duration
    ts_list = []
    for _ in range(2):
        num_packets = int(float(args.bandwidth) * (5000/5)) 
        ts_list.extend(np.linspace(begin,end, num=num_packets, endpoint=False))
        begin +=duration
        end +=duration

        num_packets_ = int(float(args.bandwidth)/2 * (5000/5))
        ts_list.extend(np.linspace(begin,end, num=num_packets_, endpoint=False))
        begin +=duration
        end +=duration

    # trace path
    make_sure_path_exists(args.output_dir)
    trace_path = path.join(args.output_dir, '%smbps_jitter.trace' % args.bandwidth)

    # write timestamps to trace
    with open(trace_path, 'w') as trace:
        for ts in ts_list:
            trace.write('%d\n' % ts)


if __name__ == '__main__':
    main()
