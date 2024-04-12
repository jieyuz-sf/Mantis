import PIL
import torch
from .modeling_llava import LlavaForConditionalGeneration
from .processing_llava import MLlavaProcessor
from ..conversation import conv_mllava_v1 as default_conv
from ..conversation import conv_mllava_v1_mmtag as default_conv_mmtag

from typing import List, Tuple, Union, Tuple

def chat_mllava(
    text:str, 
    images: List[Union[PIL.Image.Image, str]], 
    model:LlavaForConditionalGeneration, 
    processor:MLlavaProcessor, 
    max_input_length:int=None, 
    history:List[dict]=None, 
    **kwargs) -> Tuple[str, List[dict]]:
    """
    Chat with the Mllava model
    Args:
        text: str, the text to be sent to the model, where <image> will be the placeholder for the image
        images: List[PIL.Image.Image], the images to be sent to the model, or None  
        model: LlavaForConditionalGeneration, the model to be used
        processor: MLlavaProcessor, the processor to be used
        max_input_length: int, the maximum input length
        history: List[dict], list of messages in the conversation as history. Each message is a dictionary {"role": "ASSISTANT/USER", "text": "the message"}. If None, the conversation will start from scratch
        kwargs: dict, the generation kwargs
    Returns:
        Tuple[str, List[dict]], the generated text and the history of the conversation
    """
    conv = default_conv.copy()
    conv.messages = []
    if history is not None:
        for message in history:
            message["role"] = message["role"].upper()
            assert message["role"] in conv.roles
            conv.append_message(message["role"], message["text"])
    else:
        history = []
    conv.append_message(conv.roles[0], text)
    conv.append_message(conv.roles[1], "")
    
    prompt = conv.get_prompt()
    if images:
        for i in range(len(images)):
            if isinstance(images[i], str):
                images[i] = PIL.Image.open(images[i])
    
    inputs = processor(images=images, text=prompt, return_tensors="pt", truncation=isinstance(max_input_length, int), max_length=max_input_length)
    for k, v in inputs.items():
        if v is not None:
            if isinstance(v, torch.Tensor):
                inputs[k] = v.to(model.device)
            elif isinstance(v, list):
                inputs[k] = [x.to(model.device) for x in v]
            else:
                raise ValueError(f"Invalid input type: {type(v)}")

    if not "max_length" in kwargs and not "max_new_tokens" in kwargs:
        kwargs["max_length"] = 4096
    
    output_ids = model.generate(**inputs, **kwargs)
    output_ids = output_ids[0]
    
    # remove the input tokens
    generated_ids = output_ids[inputs["input_ids"].shape[-1]:]
    generated_text = processor.decode(generated_ids, skip_special_tokens=True)

    history.append({"role": conv.roles[0], "text": text})
    history.append({"role": conv.roles[1], "text": generated_text})
    
    return generated_text, history


def chat_mllava_stream(
    text:str, 
    images: List[Union[PIL.Image.Image, str]], 
    model:LlavaForConditionalGeneration, 
    processor:MLlavaProcessor, 
    max_input_length:int=None, 
    history:List[dict]=None, 
    **kwargs) -> Tuple[str, List[dict]]:
    """
    Chat with the Mllava model
    Args:
        text: str, the text to be sent to the model, where <image> will be the placeholder for the image
        images: List[PIL.Image.Image], the images to be sent to the model, or None  
        model: LlavaForConditionalGeneration, the model to be used
        processor: MLlavaProcessor, the processor to be used
        max_input_length: int, the maximum input length
        history: List[dict], list of messages in the conversation as history. Each message is a dictionary {"role": "ASSISTANT/USER", "text": "the message"}. If None, the conversation will start from scratch
        kwargs: dict, the generation kwargs
    Returns:
        Tuple[str, List[dict]], the generated text and the history of the conversation
        

    """
    conv = default_conv.copy()
    conv.messages = []
    if history is not None:
        for message in history:
            message["role"] = message["role"].upper()
            assert message["role"] in conv.roles
            conv.append_message(message["role"], message["text"])
    else:
        history = []
    conv.append_message(conv.roles[0], text)
    conv.append_message(conv.roles[1], "")
    
    prompt = conv.get_prompt()
    if images:
        for i in range(len(images)):
            if isinstance(images[i], str):
                images[i] = PIL.Image.open(images[i])
    
    inputs = processor(images=images, text=prompt, return_tensors="pt", truncation=True, max_length=max_input_length)
    for k, v in inputs.items():
        if v is not None:
            if isinstance(v, torch.Tensor):
                inputs[k] = v.to(model.device)
            elif isinstance(v, list):
                inputs[k] = [x.to(model.device) for x in v]
            else:
                raise ValueError(f"Invalid input type: {type(v)}")
    
    from transformers import TextIteratorStreamer
    from threading import Thread
    streamer = TextIteratorStreamer(processor, skip_prompt=True, skip_special_tokens=True)
    kwargs["streamer"] = streamer
    inputs.update(kwargs)
    thread = Thread(target=model.generate, kwargs=inputs)
    thread.start()
    history.append({"role": conv.roles[0], "text": text})
    history.append({"role": conv.roles[1], "text": ""})
    for _output in streamer:
        history[-1]["text"] += _output
        yield history[-1]["text"], history