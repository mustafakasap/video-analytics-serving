'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import os
import shutil
import requests
import subprocess
import tempfile
import shlex
import config as cfg
from pathlib import Path
from utils import create_convert_command
from utils import create_download_command
from utils import create_directory
from utils import load_document
from utils import print_action

def find_model_root(model,output_dir):
    for root, directories, files in os.walk(output_dir):
        if model in directories:
            return os.path.abspath(os.path.join(root,model))
    return None

def find_model_proc(model):
    if os.path.isdir(cfg.model_proc_root):
        for root, directories, files in os.walk(cfg.model_proc_root):
            for filepath in files:
                if os.path.splitext(filepath)[0] == model:
                    return os.path.join(root,filepath)
    else:
        url = cfg.base_gst_video_analytics_repo_url + '{0}.json'.format(model)
        r = requests.get(url)

        if r.status_code == 200:
            with open('{0}.json'.format(model), 'wb') as f:
                f.write(r.content)
            print("Downloaded {0} model-proc file from gst-video-analytics repo".format(model))
        else:
            print("Warning, model-proc not found in gst-video-analytics repo.")
            print("Creating empty json file for {0} to allow model to load in VA-Serving".format(model))
            print("Do not specify model-proc in pipeline that utilizes this model")
            Path('./{0}.json'.format(model)).touch()

        return os.path.abspath('{0}.json'.format(model))

def download_and_convert_model(target_root, model, force):
    if isinstance(model, dict):
        model_name = model.get('model', None)
        if model_name != None:
            target_model = os.path.join(target_root, model_name)
        else:
            print("Model name not present for {0}. Skipping this model.".format(model))
            return
        model_version = model.get('version', None)
        if model_version != None:
            target_model = os.path.join(target_model, str(model_version))
        else:
            target_model = os.path.join(target_model, "1")
    else:
        model_name = model
        target_model = os.path.join(os.path.join(target_root, model_name), "1")

    if (not force) and (os.path.isdir(target_model)):
        print("Model Directory {0} Exists - Skipping".format(model_name))
        return
        
    with tempfile.TemporaryDirectory() as output_dir:
        command = create_download_command(model_name,output_dir)
        print(' '.join(command))
        result = subprocess.run(command)
        if result.returncode != 0:
            return
        command = create_convert_command(model_name,output_dir)
        print(' '.join(command))
        subprocess.run(command)
        
        model_path = find_model_root(model_name,output_dir)

        for filename in os.listdir(model_path):
            if os.path.isdir(os.path.join(model_path,filename)):
                if os.path.isdir(os.path.join(target_model,filename)):
                    shutil.rmtree(os.path.join(target_model,filename))
                shutil.move(os.path.join(model_path,filename),os.path.join(target_model,filename))
       
        model_proc = find_model_proc(model_name)
        shutil.move(model_proc, os.path.join(target_model, '{}.json'.format(model_name)))
            
        
def download(model_list_path, output_dir, force):     
    model_list = load_document(model_list_path)
    if model_list == None:
        print("Exception while loading yaml file. File could be malformed. Please check the format and retry.")
        return

    target_root = os.path.join(output_dir,"models")
    
    create_directory(target_root,False)

    for model in model_list:
        download_and_convert_model(target_root, model, force)