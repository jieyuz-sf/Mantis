#!/bin/bash
#. /export/share/jieyu/.bashrc

export HF_HOME=/export/share/jieyu/cache/


## change for each ablation run
export DATA_CONFIG=/export/share/jieyu/mantis_data/$1
echo $1

export RUN_NAME=$2
echo $2


## if use salesforce wandb
#wandb login --relogin --host=https://salesforceairesearch.wandb.io local-cc31cf0394e6bb2f7f2a9ed4358a392e544c6b54 --relogin

## activate llava environment
source /export/share/zixianma/miniconda/bin/activate
conda activate mantis

cd /export/share/jieyu/Mantis/mantis/train
bash scripts/train_mllava_mma.sh $2

/export/share/jieyu/VLMEvalKit-mantis/eval.sh $2 $3
