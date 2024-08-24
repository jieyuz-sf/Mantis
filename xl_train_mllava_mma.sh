#!/bin/bash
#. /export/agentstudio-family/zixian/.bashrc
set -e

source /export/agentstudio-family/zixian/.bashrc

# export WANDB_PROJECT="zixian-ma" ## set up wandb prject name
export ROOT_DIR="/export/agentstudio-family/zixian/Mantis"

## change for each run
# export RUN_NAME="xlearner_test" #$1
# echo $1

## activate llava environment
source /export/share/zixianma/miniconda/bin/activate
conda activate /export/share/zixianma/miniconda/envs/mantis

wandb login --relogin --host=https://api.wandb.ai da9468672e669cf81d9b02408f58d3b7d4d51da9

cd /export/agentstudio-family/zixian/Mantis/mantis/train
bash scripts/train_mllava_mma.sh "mllava_50k_5e_5_decay"