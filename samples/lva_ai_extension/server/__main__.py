'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: MIT License
'''

'''
* MIT License
*
* Copyright (c) Microsoft Corporation.
*
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the Software is
* furnished to do so, subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included in all
* copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
* AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
* LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
* OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
* SOFTWARE
'''
import os
import json
import time
import resource
import subprocess
import argparse
import shutil
import gi
from queue import Queue
from gstgva.util import libgst, gst_buffer_data, GVAJSONMeta
from gstgva.video_frame import VideoFrame
from threading import Thread
from contextlib import contextmanager
from vaserving.vaserving import VAServing
from media_graph_extension import MediaGraphExtension
import grpc
import extension_pb2_grpc
from concurrent import futures

def parse_args(args=None, program_name="VA Serving AI Extension"):

    parser = argparse.ArgumentParser(prog=program_name,fromfile_prefix_chars='@',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-p", action="store", dest="port",
                        help='Port number to serve gRPC server',
                        type=int, default=int(os.getenv('PORT', "5001")))

    parser.add_argument("--pipeline-name", action="store",
                        dest="pipeline",
                        help='name of the pipeline to run',
                        type=str, default=os.getenv('PIPELINE_NAME',
                                                    'object_detection'))

    parser.add_argument("--pipeline-version", action="store",
                        dest="version",
                        help='name of the pipeline to run',
                        type=str, default=os.getenv('PIPELINE_VERSION',
                                                    'person_vehicle_bike_detection'))


    if (isinstance(args, dict)):
        args = ["--{}={}".format(key, value)
                for key, value in args.items() if value]

    return parser.parse_args(args)


if __name__ == "__main__":

    args = parse_args()
    try:
        VAServing.start({'log_level': 'INFO', "ignore_init_errors":True})
    
        
        # create gRPC server and start running
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=3))
        extension_pb2_grpc.add_MediaGraphExtensionServicer_to_server(
            MediaGraphExtension(args.pipeline, args.version), server)
        print("Pipeline Name", args.pipeline)
        print("Pipeline Version", args.version)
        server.add_insecure_port(f'[::]:{args.port}')
        print("Starting Protocol Server Application on port", args.port)
        server.start()
        server.wait_for_termination()
        VAServing.stop()

    except:
        VAServing.stop()
        exit(-1)
