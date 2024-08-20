#!/bin/bash

# Function to start FunASR service inside a Docker container
start_service() {
    local service_name=$1

    echo "Starting service for ${service_name}..."

    # Execute the following commands inside the Docker container
    docker-compose exec ${service_name} bash -c "
    cd FunASR/runtime && \
    nohup bash run_server_2pass.sh \
     --model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-onnx \
     --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx \
     --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx \
     --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx \
     --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst \
     --itn-dir thuduj12/fst_itn_zh \
     --certfile 0 \
     --hotword ../../hotwords.txt > log.txt 2>&1 &
    "

    echo "Service for ${service_name} started successfully."
}

# Start FunASR Interview service
start_service "funasr_interview"

# Start FunASR Rookie service
start_service "funasr_rookie"

echo "All services have been started."
