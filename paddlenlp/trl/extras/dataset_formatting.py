# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
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

# https://github.com/huggingface/trl/blob/c10cc8995b6fd45f3a876ec98cade97251abe733/trl/extras/dataset_formatting.py#L74

import logging
from typing import Callable, Literal, Optional, Union

from datasets import Dataset, Value

from ...transformers import AutoTokenizer

FORMAT_MAPPING = {
    "chatml": [{"content": Value(dtype="string", id=None), "role": Value(dtype="string", id=None)}],
    "instruction": {"completion": Value(dtype="string", id=None), "prompt": Value(dtype="string", id=None)},
    "paddlenlp": {"src": Value(dtype="string", id=None), "tgt": Value(dtype="string", id=None)},
}


def conversations_formatting_function(tokenizer: AutoTokenizer, messages_field: Literal["messages", "conversations"]):
    r"""
    return a callable function that takes in a "messages" dataset and returns a formatted dataset, based on the tokenizer
    apply chat template to the dataset
    """

    def format_dataset(examples):
        if isinstance(examples[messages_field][0], list):
            output_texts = []
            for i in range(len(examples[messages_field])):
                output_texts.append(tokenizer.apply_chat_template(examples[messages_field][i], tokenize=False))
            return output_texts
        else:
            return tokenizer.apply_chat_template(examples[messages_field], tokenize=False)

    return format_dataset


def instructions_formatting_function(tokenizer: AutoTokenizer):
    r"""
    return a callable function that takes in an "instructions" dataset and returns a formatted dataset, based on the tokenizer
    apply chat template to the dataset
    """

    def format_dataset(examples):
        if isinstance(examples["prompt"], list):
            output_texts = []
            for i in range(len(examples["prompt"])):
                converted_sample = [
                    {"role": "user", "content": examples["prompt"][i]},
                    {"role": "assistant", "content": examples["completion"][i]},
                ]
                output_texts.append(tokenizer.apply_chat_template(converted_sample, tokenize=False))
            return output_texts
        else:
            converted_sample = [
                {"role": "user", "content": examples["prompt"]},
                {"role": "assistant", "content": examples["completion"]},
            ]
            return tokenizer.apply_chat_template(converted_sample, tokenize=False)

    return format_dataset


def paddlenlp_instructions_formatting_function(tokenizer: AutoTokenizer):
    r"""
    return a callable function that takes in an "instructions" dataset and returns a formatted dataset, based on the tokenizer
    apply chat template to the dataset
    """

    def format_dataset(examples):
        if isinstance(examples["src"], list):
            output_texts = []
            for i in range(len(examples["src"])):
                converted_sample = [
                    {"role": "user", "content": examples["src"][i]},
                    {"role": "assistant", "content": examples["tgt"][i]},
                ]
                output_texts.append(tokenizer.apply_chat_template(converted_sample, tokenize=False))
            return output_texts
        else:
            converted_sample = [
                {"role": "user", "content": examples["src"]},
                {"role": "assistant", "content": examples["tgt"]},
            ]
            return tokenizer.apply_chat_template(converted_sample, tokenize=False)

    return format_dataset


def get_formatting_func_from_dataset(dataset: Union[Dataset], tokenizer: AutoTokenizer) -> Optional[Callable]:
    r"""
    Finds the correct formatting function based on the dataset structure. Currently supported datasets are:
    - `ChatML` with [{"role": str, "content": str}]
    - `instruction` with [{"prompt": str, "completion": str}]

    Args:
        dataset (Dataset): User dataset
        tokenizer (AutoTokenizer): Tokenizer used for formatting

    Returns:
        Callable: Formatting function if the dataset format is supported else None
    """
    if isinstance(dataset, Dataset):
        if "messages" in dataset.features:
            if dataset.features["messages"] == FORMAT_MAPPING["chatml"]:
                logging.info("Formatting dataset with chatml format")
                return conversations_formatting_function(tokenizer, "messages")
        if "conversations" in dataset.features:
            if dataset.features["conversations"] == FORMAT_MAPPING["chatml"]:
                logging.info("Formatting dataset with chatml format")
                return conversations_formatting_function(tokenizer, "conversations")
        elif dataset.features == FORMAT_MAPPING["instruction"]:
            logging.info("Formatting dataset with instruction format")
            return instructions_formatting_function(tokenizer)
        elif dataset.features == FORMAT_MAPPING["paddlenlp"]:
            return paddlenlp_instructions_formatting_function(tokenizer)

    return None