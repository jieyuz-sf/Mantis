#!/bin/bash
#. /export/share/jieyu/.bashrc

export HF_HOME=/export/share/jieyu/cache/


## activate llava environment
source /export/share/zixianma/miniconda/bin/activate
conda activate mantis

cd /export/share/jieyu/Mantis/mantis/benchmark

# for m in v4-0.05b  v4-0.1b v4-0.2b v4-both-0.05b  v4-both-0.2b  v4-both-0.1b  v4-mc-0.05b  v4-mc-0.2b v4-mc-0.1b
# for m in v4-0.5b v4-both-0.5b v4-mc-0.5b

# for m in v4-all-both-0.2b v4-all-both-sz-0.2b
for m in dc-both-0.05 dc-both-0.1 dc-both-0.2 dc-both-0.5
do
  bash eval_single_model.sh /export/share/jieyu/mantis_ckpt/Mantis-8B-siglip-llama3-pretraind/$m/checkpoint-final
done

# for m in v4-sz-0.05b  v4-sz-0.1b v4-sz-0.2b v4-sz-0.5b
# do
#   bash eval_single_model.sh /export/share/jieyu/mantis_ckpt/Mantis-8B-siglip-llama3-pretraind/$m/checkpoint-final
# done

# for m in v4-both-sz-0.05b  v4-both-sz-0.1b  v4-both-sz-0.2b  v4-both-sz-0.5b
# do
#   bash eval_single_model.sh /export/share/jieyu/mantis_ckpt/Mantis-8B-siglip-llama3-pretraind/$m/checkpoint-final
# done

# for m in v4-mc-sz-0.05b  v4-mc-sz-0.1b  v4-mc-sz-0.2b  v4-mc-sz-0.5b
# do
#   bash eval_single_model.sh /export/share/jieyu/mantis_ckpt/Mantis-8B-siglip-llama3-pretraind/$m/checkpoint-final
# done
