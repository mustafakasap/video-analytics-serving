#!/bin/bash

SERVER_IP=127.0.0.1
SERVER_PORT=5001
LVA_ROOT=/home/video-analytics-serving/samples/lva_ai_extension
SAMPLE_FILE_PATH=$LVA_ROOT/sampleframes/sample01.png
SHARED_MEMORY=
IMAGE=video-analytics-serving-lva-ai-extension:latest

#Get options passed into script
function get_options {
  while :; do
    case $1 in
      -h | -\? | --help)
        show_help
        exit
        ;;
      --server-ip)
        if [ "$2" ]; then
          SERVER_IP=$2
          shift
        else
          error "--server-ip expects a value"
        fi
        ;;
      --server-port)
        if [ "$2" ]; then
          SERVER_PORT=$2
          shift
        else
          error "--server-port expects a value"
        fi
        ;;
      --shared-memory)
        SHARED_MEMORY="-m"
	shift
        ;;
      --sample-file-path)
        if [ "$2" ]; then
          SAMPLE_FILE_PATH=$2
          shift
        else
          error "--sample-file-path expects a value"
        fi
        ;;
      *)
        break
        ;;
    esac

    shift
  done
}

function show_help {
  echo "usage: ./run_client.sh"
  echo "  [ --server-ip : Specify the server ip to connect to ]"
  echo "  [ --server-port : Specify the server port to connect to ] "
  echo "  [ --shared-memory : Enables and uses shared memory between client and server ] "
  echo "  [ --sample-file-path : Specify the sample file path to run(file must be inside container or in volume mounted path)] "
}

function error {
    printf '%s\n' "$1" >&2
    exit
}

get_options "$@"
RUN_COMMAND="python3 $LVA_ROOT/client -s $SERVER_IP:$SERVER_PORT -l 1 $SHARED_MEMORY -f $SAMPLE_FILE_PATH"

docker run -it --rm --network=host -v /dev/shm:/dev/shm --user openvino --entrypoint /bin/bash $IMAGE -c "$RUN_COMMAND"
