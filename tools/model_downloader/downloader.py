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
from pathlib import Path
from jsonschema import Draft7Validator, FormatChecker
import config as cfg
from utils import create_convert_command
from utils import create_download_command
from utils import create_directory
from utils import load_document

def find_model_root(model, output_dir):
    for root, directories, files in os.walk(output_dir):
        if model in directories:
            return os.path.abspath(os.path.join(root, model))
    return None

def find_model_proc(model):
    if os.path.isdir(cfg.model_proc_root):
        for root, directories, files in os.walk(cfg.model_proc_root):
            for filepath in files:
                if os.path.splitext(filepath)[0] == model:
                    return os.path.join(root, filepath)
    else:
        url = cfg.base_gst_video_analytics_repo_url + '{0}.json'.format(model)
        r = requests.get(url)

        if r.status_code == 200:
            with open('/tmp/{0}.json'.format(model), 'wb') as f:
                f.write(r.content)
            print("Downloaded {0} model-proc file from gst-video-analytics repo".format(model))
        else:
            print("Warning, model-proc not found in gst-video-analytics repo.")
            print("Creating empty json file for {0} to allow model to load in VA-Serving".format(model))
            print("Do not specify model-proc in pipeline that utilizes this model")
            Path('/tmp/{0}.json'.format(model)).touch()

        return os.path.abspath('/tmp/{0}.json'.format(model))

def validate_schema(model_list):
    schema = {
        "type" : "array",
        "items" : {
            "oneOf": [
                {
                    "type" : "object",
                    "properties" : {
                        "model" : {"type" : "string"},
                        "alias" : {"type" : "string"},
                        "version" : {"type" : ["string", "integer"]},
                        "precision" : {
                            "type" : "array",
                            "items" : {"enum" : ["FP32", "FP16", "INT8", "FP16-INT8", "FP32-INT8", "FP32-INT1", "FP16-INT1", "INT1"]}
                        }
                    },
                    "required" : ["model"],
                    "additionalProperties": False
                },
                {
                    "type" : "string"
                }
            ]
        }
    }
    try:
        validator = Draft7Validator(schema, format_checker=FormatChecker())
        validator.validate(model_list)
    except Exception as err:
        print("Yaml input schema validation error.")
        print(err)
        exit(1)

def download_and_convert_model(target_root, model, force):
    precisions = None
    if isinstance(model, dict):
        model_name = model.get('model')
        alias = model.get('alias', None)
        precisions = model.get('precision', None)
        if alias != None:
            target_model = os.path.join(target_root, alias)
        else:
            target_model = os.path.join(target_root, model_name)

        model_version = model.get('version', None)
        if model_version != None:
            target_model = os.path.join(target_model, str(model_version))
        else:
            target_model = os.path.join(target_model, "1")
    else:
        model_name = model
        target_model = os.path.join(os.path.join(target_root, model_name), "1")

    if (not force) and (os.path.isdir(target_model)):
        print("Model Directory {0} Exists - Skipping".format(target_model))
        return
        
    with tempfile.TemporaryDirectory() as output_dir:
        command = create_download_command(model_name, output_dir, precisions)
        print(' '.join(command))
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            print("Error occured while downloading {0} model.".format(model_name))
            print("Please remove from input yml file and try again.")
            exit(1)
        command = create_convert_command(model_name, output_dir, precisions)
        print(' '.join(command))
        subprocess.run(command, check=False)
        
        model_path = find_model_root(model_name, output_dir)

        if os.path.isdir(target_model):
            #print("Directory {0} already exists, overwriting it.".format(target_model))
            shutil.rmtree(target_model)
        for filename in os.listdir(model_path):
            if os.path.isdir(os.path.join(model_path, filename)):
                shutil.move(os.path.join(model_path, filename), os.path.join(target_model, filename))
       
        model_proc = find_model_proc(model_name)
        shutil.move(model_proc, os.path.join(target_model, '{}.json'.format(model_name)))
            
        
def download(model_list_path, output_dir, force):     
    model_list = load_document(model_list_path)
    if model_list == None:
        exit(1)

    validate_schema(model_list)

    target_root = os.path.join(output_dir, "models")
    
    create_directory(target_root, False)

    for model in model_list:
        download_and_convert_model(target_root, model, force)
