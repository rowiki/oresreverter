#!/usr/bin/python3
# -*- coding: utf-8  -*-

from .base import ModelConfig
from .ores import OresConfig, OresDamagingConfig, OresGoodfaithConfig
from .revertrisk import MultilingualConfig, AgnosticConfig
import json
from typing import Tuple
import requests

def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])

def get_model(name: str="ores") -> ModelConfig:
	models = all_subclasses(ModelConfig)
	for model in models:
		#print(model.get_name())
		if name == model.get_name():
			return model()
	else:
		return None
