#!/bin/bash
#. /export/share/jieyu/.bashrc

export HF_HOME=/export/share/jieyu/cache/


## activate llava environment
source /export/share/zixianma/miniconda/bin/activate
conda activate mantis

cd /export/share/jieyu/Mantis/mantis/benchmark

for m in v4-0.05b  v4-0.1b v4-0.2b v4-both-0.05b  v4-both-0.2b  v4-both-0.1b  v4-mc-0.05b  v4-mc-0.2b v4-mc-0.1b
do
  bash eval_single_model.sh /export/share/jieyu/mantis_ckpt/Mantis-8B-siglip-llama3-pretraind/$m/checkpoint-final
done
