import fire
import os
import datasets
import zipfile
from pathlib import Path
from typing import List
from typing import List
from io import BytesIO
from PIL import Image
import requests
import json
from pathlib import Path
from tqdm import tqdm
from huggingface_hub import HfApi

def load_image(image_file):
    post_fixs = [".jpg", ".png", ".jpeg", ".gif"]
    if image_file is None:
        return None
    if isinstance(image_file, Image.Image):
        return image_file
    image_file = Path(image_file)
    if not image_file.exists() and not image_file.is_file():
        if all([not image_file.with_suffix(post_fix).exists() for post_fix in post_fixs]):
            raise FileNotFoundError(f"Cannot find image file {image_file}")
        else:
            for post_fix in post_fixs:
                if image_file.with_suffix(post_fix).exists():
                    image_file = image_file.with_suffix(post_fix)
                    break
                
    if not isinstance(image_file, str):
        image_file = str(image_file)
    if image_file.startswith("http"):
        response = requests.get(image_file)
        image = Image.open(BytesIO(response.content)).convert("RGB")
    else:
        import os
        try:
            image = Image.open(image_file).convert("RGB")
        except Exception as e:
            print(f"Cannot open image file {image_file}")
            raise e
    return image


def load_images(image_files):
    if not isinstance(image_files, list):
        return load_image(image_files)
    out = []
    for image_file in tqdm(image_files, desc="Loading images", disable=len(image_files) < 1000):
        if isinstance(image_file, Image.Image):
            image = image_file
        else:
            image = load_image(image_file)
        out.append(image)
    return out



def create_hf_dataset(dataset:List[dict], split):
    """
    dataset is a list of dict, each dict is a sample
    {
        "id": "0",
        "images": [PIL.Image.Image, PIL.Image.Image, ...],
        "conversations": [
            {
                "role": "user",
                "content": "hello, how are you?"
            },
            ...
        ]
    }
    this function will create a hf dataset
    Args:
        dataset (List[dict]): _description_
    """
    print("Creating hf dataset...")
    hf_dataset = datasets.Dataset.from_list(
        dataset,
        features=datasets.Features(
            {
                "id": datasets.Value("string"),
                "images": datasets.Sequence(datasets.Image()),
                "question_type": datasets.Value("string"),
                "question": datasets.Value("string"),
                "options": datasets.Sequence(datasets.Value("string")),
                "answer": datasets.Value("string"),
                "data_source": datasets.Value("string"),
                "category": datasets.Value("string"),
            }
        ),
        split=split,
    )
    return hf_dataset

def main(
    dataset_file: str,
    dataset_name: str,
    split: str,
    repo_id: str,
    image_upload_mode:str="parquet",
    num_parts: int=1,
    image_dir: str=None,
):
    """
    if image_upload_mode is "zip", then the images will be zipped and uploaded to hf under ./{dataset_name}/{split}_images.zip through upload_file
        This mode does not require load images in the memory and is faster.
        This mode requires the hugging face dataset has a `repo_name.py` file that contains the same code as `miqa_dataset.py` in this folder.
    if image_upload_mode is "parquet", then the images will be loaded into the dataset and upload through push_to_hub.
        This mode requires load images in the memory (OOM risk) and dataset transformation as well as the uploading is also slower (might take hours).
    """
    token = os.environ.get("HF_TOKEN", None)
    
    if not isinstance(dataset_file, Path):
        dataset_file = Path(dataset_file)
    if image_dir is not None and not isinstance(image_dir, Path):
        image_dir = Path(image_dir)
    with open(dataset_file) as f:
        dataset = json.load(f)
    
    assert image_upload_mode in ["zip", "parquet"], f"image_upload_mode must be zip or parquet, but got {image_upload_mode}"
    num_parts = num_parts if image_upload_mode == "parquet" else 1
    
    # load images
    all_split_image_paths = []
    part_size = len(dataset) // num_parts + 1
    for part_id in range(num_parts):
        print(f"Processing part {part_id}...")
        part_start_idx = part_id * part_size
        part_end_idx = min((part_id + 1) * part_size, len(dataset))
        sub_dataset = dataset[part_start_idx:part_end_idx]
        part_data = []
        for item in tqdm(sub_dataset, desc="Processing dataset"):
            if image_dir is None or 'images' not in item or len(item['images']) == 0:
                images = None
            else:
                image_paths = item['images'] 
                image_paths = [Path(path) for path in image_paths]
                image_paths = [dataset_file.parent / path for path in image_paths]
                all_split_image_paths.extend(image_paths)
                if not all([path.exists() for path in image_paths]):
                    print(f"Cannot find image files {image_paths}")
                    continue
                
                if image_upload_mode == "parquet":
                    images = load_images(image_paths)
                elif image_upload_mode == "zip":
                    images = [str(path.relative_to(image_dir)) for path in image_paths]
                else:
                    raise ValueError(f"image_upload_mode must be zip or parquet, but got {image_upload_mode}")
            
            part_data.append({
                "id": item["id"],
                "question_type": item["question_type"],
                "question": item["question"],
                "images": images,
                "options": item["options"],
                "answer": item["answer"],
                "data_source": item["data_source"],
                "category": item["category"],
            })
        
        # set split
        if num_parts == 1:
            part_split = split
        elif num_parts > 1:
            part_split = f"{split}_part_{part_id}"
            
        # create hf dataset    
        hf_dataset = create_hf_dataset(part_data, part_split)
        
        # upload hugingface dataset
        print(f"Uploading to part {dataset_name}:{part_split} to {repo_id}...")
        hf_dataset.push_to_hub(
            repo_id=repo_id,
            config_name=dataset_name,
            split=part_split,
            token=token,
            commit_message=f"Add {dataset_name} {part_split} dataset",
        )
        del hf_dataset
        del part_data
    
    
    # zip image files and upload to hf under ./{dataset_name}/train_images.zip
    all_split_image_paths = list(set(all_split_image_paths))
    if image_dir is not None and image_upload_mode == "zip":
        api = HfApi()
        print(f"Zipping image files in {image_dir}...")
        zip_file = Path(f"{dataset_name}_{split}_images.zip")
        zip_file.unlink(missing_ok=True)
        zip_file = str(zip_file)
        try:
            with zipfile.ZipFile(zip_file, "w") as zf:
                for image_file in tqdm(all_split_image_paths, desc="Zipping images"):
                    zf.write(image_file, arcname=str(image_file.relative_to(image_dir)))
            print(f"Uploading to {repo_id}...")
            api.upload_file(
                path_or_fileobj=zip_file,
                path_in_repo=f"{dataset_name}/{split}_images.zip",
                repo_id=repo_id,
                token=token,
                repo_type="dataset",
                commit_message=f"Add {dataset_name} {split} images",
            )
        finally:
            os.remove(zip_file)
            
    print("Done!")
    
    
if __name__ == "__main__":
    fire.Fire(main)