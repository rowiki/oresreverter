#!/usr/bin/python3
# -*- coding: utf-8  -*-

import json
import pywikibot
import requests
from .base import RevertModelConfig


class RevertriskBaseConfig(RevertModelConfig):
	def __init__(self):
		self.url = "https://api.wikimedia.org/service/lw/inference/v1/models/{model}:predict"
		self.type = None
		self.threshold = 0.909 # TODO

	def likely_bad(self, score:float) -> bool:
		return score >= self.threshold

	def possibly_bad(self, score:float) -> bool:
		return score >= self.threshold - 0.1

	def likely_constructive(self, score:float) -> bool:
		return score <= 1 - self.threshold

	def get_score(self, lang: str, revid: int) -> float:
		score, _ = self.get_result(lang, revid)
		return score

	def get_result(self, lang: str, revid: int) -> (float, bool):
		score = None
		prediction = False
		url = self.url.format(model=self.type)
		headers = {'Content-Type': 'application/json', 'User-Agent': 'PatrocleBot (patroclebot@strainu.ro)' }
		data = {"lang": lang, "rev_id": revid}
		r = requests.post(url=url, headers=headers, data=json.dumps(data))
		if r.status_code != 200:
			pywikibot.error(f"Obtaining the {self.get_name()} score for revision {revid} from {url} failed with code {r.status_code}")
			return 0, None
		try:
			resp = r.json()
			score = resp["output"]["probabilities"]["true"]
			prediction = resp["output"]["prediction"]
		except Exception as e:
			raise ValueError(f"Obtaining the {self.get_name()} score for revision {revid} failed with error {e}. URL was {url}")
		finally:
			r.close()
			return score, prediction

class MultilingualConfig(RevertriskBaseConfig):
	"""Configuration for the multilingual revert risk model."""
	def __init__(self):
		super(MultilingualConfig, self).__init__()
		self.type = "revertrisk-multilingual"
		self.docs = ":m:Machine_learning_models/Proposed/Multilingual_revert_risk"

	@staticmethod
	def get_name() -> str:
		return "revertrisk.multilingual"

class AgnosticConfig(RevertriskBaseConfig):
	"""Configuration for the language agnostic revert risk model."""
	def __init__(self):
		super(AgnosticConfig, self).__init__()
		self.type = "revertrisk-language-agnostic"
		self.docs = ":m:Machine_learning_models/Proposed/Language-agnostic_revert_risk"

	@staticmethod
	def get_name() -> str:
		return "revertrisk.agnostic"
