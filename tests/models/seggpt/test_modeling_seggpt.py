# coding=utf-8
# Copyright 2023 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Testing suite for the PyTorch SegGpt model. """


import inspect
import unittest

from datasets import load_dataset

from transformers import SegGptConfig
from transformers.testing_utils import (
    require_torch,
    require_vision,
    slow,
    torch_device,
)
from transformers.utils import cached_property, is_torch_available, is_vision_available

from ...test_configuration_common import ConfigTester
from ...test_modeling_common import ModelTesterMixin, floats_tensor
from ...test_pipeline_mixin import PipelineTesterMixin


if is_torch_available():
    import torch
    from torch import nn

    from transformers import SegGptForImageSegmentation, SegGptModel
    from transformers.models.seggpt.modeling_seggpt import SEGGPT_PRETRAINED_MODEL_ARCHIVE_LIST


if is_vision_available():
    from transformers import SegGptImageProcessor


class SegGptModelTester:
    def __init__(
        self,
        parent,
        batch_size=2,
        image_size=30,
        patch_size=2,
        num_channels=3,
        is_training=False,
        use_labels=True,
        hidden_size=32,
        num_hidden_layers=2,
        num_attention_heads=4,
        hidden_act="gelu",
        hidden_dropout_prob=0.1,
        attention_probs_dropout_prob=0.1,
        initializer_range=0.02,
        mlp_ratio=2.0,
        merge_index=0,
        output_indicies=[1],
        pretrain_image_size=10,
        decoder_hidden_size=10,
    ):
        self.parent = parent
        self.batch_size = batch_size
        self.image_size = image_size
        self.patch_size = patch_size
        self.num_channels = num_channels
        self.is_training = is_training
        self.use_labels = use_labels
        self.hidden_size = hidden_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.hidden_act = hidden_act
        self.hidden_dropout_prob = hidden_dropout_prob
        self.attention_probs_dropout_prob = attention_probs_dropout_prob
        self.initializer_range = initializer_range
        self.mlp_ratio = mlp_ratio
        self.merge_index = merge_index
        self.output_indicies = output_indicies
        self.pretrain_image_size = pretrain_image_size
        self.decoder_hidden_size = decoder_hidden_size

        # in SegGpt, the seq length equals the number of patches (we don't use the [CLS] token)
        num_patches = (image_size // patch_size) ** 2
        self.seq_length = num_patches

    def prepare_config_and_inputs(self):
        pixel_values = floats_tensor([self.batch_size, self.num_channels, self.image_size // 2, self.image_size])
        prompt_pixel_values = floats_tensor(
            [self.batch_size, self.num_channels, self.image_size // 2, self.image_size]
        )
        prompt_masks = floats_tensor([self.batch_size, self.num_channels, self.image_size // 2, self.image_size])

        labels = None
        if self.use_labels:
            labels = floats_tensor([self.batch_size, self.num_channels, self.image_size // 2, self.image_size])

        config = self.get_config()

        return config, pixel_values, prompt_pixel_values, prompt_masks, labels

    def get_config(self):
        return SegGptConfig(
            image_size=self.image_size,
            patch_size=self.patch_size,
            num_channels=self.num_channels,
            hidden_size=self.hidden_size,
            num_hidden_layers=self.num_hidden_layers,
            num_attention_heads=self.num_attention_heads,
            hidden_act=self.hidden_act,
            hidden_dropout_prob=self.hidden_dropout_prob,
            initializer_range=self.initializer_range,
            mlp_ratio=self.mlp_ratio,
            merge_index=self.merge_index,
            output_indicies=self.output_indicies,
            pretrain_image_size=self.pretrain_image_size,
            decoder_hidden_size=self.decoder_hidden_size,
        )

    def create_and_check_model(self, config, pixel_values, prompt_pixel_values, prompt_masks, labels):
        model = SegGptModel(config=config)
        model.to(torch_device)
        model.eval()
        result = model(pixel_values, prompt_pixel_values, prompt_masks)
        self.parent.assertEqual(
            result.last_hidden_state.shape,
            (
                self.batch_size,
                self.image_size // self.patch_size,
                self.image_size // self.patch_size,
                self.hidden_size,
            ),
        )

    def prepare_config_and_inputs_for_common(self):
        config_and_inputs = self.prepare_config_and_inputs()
        (
            config,
            pixel_values,
            prompt_pixel_values,
            prompt_masks,
            labels,
        ) = config_and_inputs
        inputs_dict = {
            "pixel_values": pixel_values,
            "prompt_pixel_values": prompt_pixel_values,
            "prompt_masks": prompt_masks,
        }
        return config, inputs_dict


@require_torch
class SegGptModelTest(ModelTesterMixin, PipelineTesterMixin, unittest.TestCase):
    """
    Here we also overwrite some of the tests of test_modeling_common.py, as SegGpt does not use input_ids, inputs_embeds,
    attention_mask and seq_length.
    """

    all_model_classes = SegGptModel, SegGptForImageSegmentation) if is_torch_available() else ()
    fx_compatible = False

    test_pruning = False
    test_resize_embeddings = False
    test_head_masking = False
    test_torchscript = False
    pipeline_model_mapping = (
        {"feature-extraction": SegGptModel, "mask-generation": SegGptModel} if is_torch_available() else {}
    )

    def setUp(self):
        self.model_tester = SegGptModelTester(self)
        self.config_tester = ConfigTester(self, config_class=SegGptConfig, has_text_modality=False)

    def test_config(self):
        self.config_tester.run_common_tests()

    @unittest.skip(reason="SegGpt does not use inputs_embeds")
    def test_inputs_embeds(self):
        pass

    def test_model_common_attributes(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            model = model_class(config)
            self.assertIsInstance(model.get_input_embeddings(), (nn.Module))

    def test_forward_signature(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            model = model_class(config)
            signature = inspect.signature(model.forward)
            # signature.parameters is an OrderedDict => so arg_names order is deterministic
            arg_names = [*signature.parameters.keys()]

            expected_arg_names = ["pixel_values", "prompt_pixel_values", "prompt_masks"]
            self.assertListEqual(arg_names[:3], expected_arg_names)

    def test_model(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_model(*config_and_inputs)

    def test_hidden_states_output(self):
        def check_hidden_states_output(inputs_dict, config, model_class):
            model = model_class(config)
            model.to(torch_device)
            model.eval()

            with torch.no_grad():
                outputs = model(**self._prepare_for_class(inputs_dict, model_class))

            hidden_states = outputs.encoder_hidden_states if config.is_encoder_decoder else outputs.hidden_states

            expected_num_layers = getattr(
                self.model_tester, "expected_num_hidden_layers", self.model_tester.num_hidden_layers + 1
            )
            self.assertEqual(len(hidden_states), expected_num_layers)

            patch_height = patch_width = config.image_size // config.patch_size

            self.assertListEqual(
                list(hidden_states[0].shape[-3:]),
                [patch_height, patch_width, self.model_tester.hidden_size],
            )

        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            inputs_dict["output_hidden_states"] = True
            check_hidden_states_output(inputs_dict, config, model_class)

            # check that output_hidden_states also work using config
            del inputs_dict["output_hidden_states"]
            config.output_hidden_states = True

            check_hidden_states_output(inputs_dict, config, model_class)

    @slow
    def test_model_from_pretrained(self):
        for model_name in SEGGPT_PRETRAINED_MODEL_ARCHIVE_LIST[:1]:
            model = SegGptModel.from_pretrained(model_name)
            self.assertIsNotNone(model)


# We will verify our results on an image of cute cats
def prepare_img():
    ds = load_dataset("EduardoPacheco/seggpt-example-data")["train"]
    images = [image.convert("RGB") for image in ds["image"]]
    masks = [image.convert("RGB") for image in ds["mask"]]
    return images, masks


"./tests/fixtures/tests_samples/COCO/000000039769.png"


@require_torch
@require_vision
class SegGptModelIntegrationTest(unittest.TestCase):
    @cached_property
    def default_image_processor(self):
        return (
            SegGptImageProcessor.from_pretrained("EduardoPacheco/seggpt-vit-large") if is_vision_available() else None
        )

    @slow
    def test_one_shot_inference(self):
        model = SegGptForImageSegmentation.from_pretrained("EduardoPacheco/seggpt-vit-large").to(torch_device)

        image_processor = self.default_image_processor

        images, masks = prepare_img()
        input_image = images[1]
        prompt_image = images[0]
        prompt_mask = masks[0]

        inputs = image_processor(
            images=input_image, prompt_images=prompt_image, prompt_masks=prompt_mask, return_tensors="pt"
        )

        # Verify pixel values
        expected_prompt_pixel_values = torch.tensor(
            [
                [[-0.6965, -0.6965, -0.6965], [-0.6965, -0.6965, -0.6965], [-0.6965, -0.6965, -0.6965]],
                [[1.6583, 1.6583, 1.6583], [1.6583, 1.6583, 1.6583], [1.6583, 1.6583, 1.6583]],
                [[2.3088, 2.3088, 2.3088], [2.3088, 2.3088, 2.3088], [2.3088, 2.3088, 2.3088]],
            ]
        )

        expected_pixel_values = torch.tensor(
            [
                [[1.6324, 1.6153, 1.5810], [1.6153, 1.5982, 1.5810], [1.5810, 1.5639, 1.5639]],
                [[1.2731, 1.2556, 1.2206], [1.2556, 1.2381, 1.2031], [1.2206, 1.2031, 1.1681]],
                [[1.6465, 1.6465, 1.6465], [1.6465, 1.6465, 1.6465], [1.6291, 1.6291, 1.6291]],
            ]
        )

        expected_prompt_masks = torch.tensor(
            [
                [[-2.1179, -2.1179, -2.1179], [-2.1179, -2.1179, -2.1179], [-2.1179, -2.1179, -2.1179]],
                [[-2.0357, -2.0357, -2.0357], [-2.0357, -2.0357, -2.0357], [-2.0357, -2.0357, -2.0357]],
                [[-1.8044, -1.8044, -1.8044], [-1.8044, -1.8044, -1.8044], [-1.8044, -1.8044, -1.8044]],
            ]
        )

        self.assertTrue(torch.allclose(inputs.pixel_values[0, :, :3, :3], expected_pixel_values, atol=1e-4))
        self.assertTrue(
            torch.allclose(inputs.prompt_pixel_values[0, :, :3, :3], expected_prompt_pixel_values, atol=1e-4)
        )
        self.assertTrue(torch.allclose(inputs.prompt_masks[0, :, :3, :3], expected_prompt_masks, atol=1e-4))

        inputs = {k: v.to(torch_device) for k, v in inputs.items()}
        # forward pass
        with torch.no_grad():
            outputs = model(**inputs)

        # verify the logits
        expected_shape = torch.Size((1, 3, 896, 448))
        self.assertEqual(outputs.pred_masks.shape, expected_shape)

        expected_slice = torch.tensor(
            [
                [[-2.1208, -2.1190, -2.1198], [-2.1237, -2.1228, -2.1227], [-2.1232, -2.1226, -2.1228]],
                [[-2.0405, -2.0396, -2.0403], [-2.0434, -2.0434, -2.0433], [-2.0428, -2.0432, -2.0434]],
                [[-1.8102, -1.8088, -1.8099], [-1.8131, -1.8126, -1.8129], [-1.8130, -1.8128, -1.8131]],
            ]
        ).to(torch_device)

        self.assertTrue(torch.allclose(outputs.pred_masks[0, :, :3, :3], expected_slice, atol=1e-4))

        result = image_processor.post_process_masks(outputs, [input_image.size[::-1]])[0]["mask"]

        result_expected_shape = torch.Size((1, 3, 170, 297))
        expected_area = 26654
        area = (torch.clip(result * 255, 0, 255).mean(dim=1) > 0).sum().item()
        self.assertEqual(result.shape, result_expected_shape)
        self.assertEqual(area, expected_area)

    @slow
    def test_few_shot_inference(self):
        model = SegGptForImageSegmentation.from_pretrained("EduardoPacheco/seggpt-vit-large").to(torch_device)
        image_processor = self.default_image_processor

        images, masks = prepare_img()
        input_images = [images[1]] * 2
        prompt_images = [images[0], images[2]]
        prompt_masks = [masks[0], masks[2]]

        inputs = image_processor(
            images=input_images, prompt_images=prompt_images, prompt_masks=prompt_masks, return_tensors="pt"
        )

        inputs = {k: v.to(torch_device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs, feature_ensemble=True)

        expected_shape = torch.Size((2, 3, 896, 448))
        expected_slice = torch.tensor(
            [
                [[-2.1201, -2.1192, -2.1189], [-2.1217, -2.1210, -2.1204], [-2.1216, -2.1202, -2.1194]],
                [[-2.0393, -2.0390, -2.0387], [-2.0402, -2.0402, -2.0397], [-2.0400, -2.0394, -2.0388]],
                [[-1.8083, -1.8076, -1.8077], [-1.8105, -1.8102, -1.8099], [-1.8105, -1.8095, -1.8090]],
            ]
        ).to(torch_device)

        self.assertEqual(outputs.pred_masks.shape, expected_shape)
        self.assertTrue(torch.allclose(outputs.pred_masks[0, :, 448:451, :3], expected_slice, atol=4e-4))
