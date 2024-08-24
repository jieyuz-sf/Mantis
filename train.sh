#!/bin/bash
#. /export/share/jieyu/.bashrc

export HF_HOME=/export/share/jieyu/cache/

#export WANDB_PROJECT="vlm-llava" ## set up wandb prject name
export ROOT_DIR="/export/share/ayan/"

## change for each ablation run
export JSON_DIR=$1
# export JSON_DIR="json_jieyu/v0_0.1.json"
echo $1

export RUN_NAME=$2
# export RUN_NAME="llava-v1.5-7b-mix-v0-0.1"
echo $2


## if use salesforce wandb
#wandb login --relogin --host=https://salesforceairesearch.wandb.io local-cc31cf0394e6bb2f7f2a9ed4358a392e544c6b54 --relogin

## activate llava environment
source /export/share/zixianma/miniconda/bin/activate
conda activate mantis

cd /export/share/ayan/VLM/LLaVA
bash scripts/v1_5/finetune_7b.sh

cd /export/share/jieyu/xgen-mm-eval-jieyu/
bash eval_llava.sh $2
