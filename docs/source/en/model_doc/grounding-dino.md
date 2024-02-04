<!--Copyright 2023 The HuggingFace Team. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.

⚠️ Note that this file is in Markdown but contain specific syntax for our doc-builder (similar to MDX) that may not be
rendered properly in your Markdown viewer.

-->

# Grounding DINO

## Overview

The Grounding DINO model was proposed in [Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection](https://arxiv.org/abs/2303.05499) by Shilong Liu, Zhaoyang Zeng, Tianhe Ren, Feng Li, Hao Zhang, Jie Yang, Chunyuan Li, Jianwei Yang, Hang Su, Jun Zhu, Lei Zhang. Grounding DINO extends a closed-set object detection model with a text encoder, enabling open-set object detection. The model achieves remarkable results, such as 52.5 AP on COCO zero-shot.

The abstract from the paper is the following:

*In this paper, we present an open-set object detector, called Grounding DINO, by marrying Transformer-based detector DINO with grounded pre-training, which can detect arbitrary objects with human inputs such as category names or referring expressions. The key solution of open-set object detection is introducing language to a closed-set detector for open-set concept generalization. To effectively fuse language and vision modalities, we conceptually divide a closed-set detector into three phases and propose a tight fusion solution, which includes a feature enhancer, a language-guided query selection, and a cross-modality decoder for cross-modality fusion. While previous works mainly evaluate open-set object detection on novel categories, we propose to also perform evaluations on referring expression comprehension for objects specified with attributes. Grounding DINO performs remarkably well on all three settings, including benchmarks on COCO, LVIS, ODinW, and RefCOCO/+/g. Grounding DINO achieves a 52.5 AP on the COCO detection zero-shot transfer benchmark, i.e., without any training data from COCO. It sets a new record on the ODinW zero-shot benchmark with a mean 26.1 AP.*

Tips:

- One can use [`GroundingDinoProcessor`] to prepare image-text pairs for the model.
- To separate classes in the text use a period e.g. "a cat. a dog."
- When using multiple classes use `post_process_grounded_object_detection` from [`GroundingDinoProcessor`] to post process outputs

```python
import requests

import torch
from PIL import Image
from transformers import AutoModelForObjectDetection, AutoProcessor

model_id = "EduardoPacheco/grounding-dino-tiny"

model = AutoModelForObjectDetection.from_pretrained(model_id).to(device)
processor = AutoProcessor.from_pretrained(model_id)

def load_image(url):
    return Image.open(requests.get(url, stream=True).raw)

image = load_image('http://images.cocodataset.org/val2017/000000039769.jpg')
# Check for cats and remote controls
text = "a cat. a remote control"

inputs = processor(images=image, text=text, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)

results = processor.post_process_grounded_object_detection(
    outputs,
    inputs.input_ids,
    bbox_threshold=0.4
    text_threshold=0.3,
    target_sizes=[image.size[::-1]]
)
```

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/grouding_dino_architecture.png"
alt="drawing" width="600"/>

<small> Grounding DINO overview. Taken from the <a href="https://arxiv.org/abs/2303.05499">original paper</a>. </small>

This model was contributed by [EduardoPacheco](https://huggingface.co/EduardoPacheco) and [nielsr](https://huggingface.co/nielsr).
The original code can be found [here](https://github.com/IDEA-Research/GroundingDINO).


## GroundingDinoImageProcessor

[[autodoc]] GroundingDinoImageProcessor
    - preprocess
    - post_process_object_detection

## GroundingDinoProcessor

[[autodoc]] GroundingDinoProcessor
    - post_process_grounded_object_detection

## GroundingDinoTextConfig

[[autodoc]] GroundingDinoTextConfig

## GroundingDinoConfig

[[autodoc]] GroundingDinoConfig

## GroundingDinoModel

[[autodoc]] GroundingDinoModel
    - forward

## GroundingDinoForObjectDetection

[[autodoc]] GroundingDinoForObjectDetection
    - forward
