#!/usr/bin/python3
# -*- coding: utf-8  -*-

import json
from typing import Tuple
import requests

class ModelConfig(object):
	"""Abstract Implementation for a generic ML model."""
	type: str
	url: str
	cfg: dict
	docs:  str # a link to the documentation of the model

	@staticmethod
	def get_name() -> str:
		return None

	def get_score(self, lang: str, revid: int) -> float:
		raise NotImplementedError

	def get_docs(self) -> str:
		return self.docs

	def set_config(self, config: dict):
		self.cfg = config

class RevertModelConfig(ModelConfig):

	def likely_bad(self, score:float) -> bool:
		raise NotImplementedError

	def possibly_bad(self, score:float) -> bool:
		raise NotImplementedError

	def likely_constructive(self, score:float) -> bool:
		raise NotImplementedError

