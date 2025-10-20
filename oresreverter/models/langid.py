#!/usr/bin/python3
# -*- coding: utf-8  -*-

import json
import pywikibot
import requests

from .base import ModelConfig


class LangIdConfig(ModelConfig):
	def __init__(self):
		self.url = "https://api.wikimedia.org/service/lw/inference/v1/models/langid:predict"
		self.type = None
		self.threshold = 0.909 # TODO
		self.docs = ":m:Machine_learning_models/Production/Language_Identification"

	def get_result(self, text: str) -> (float, str):
		score = None
		prediction = False
		headers = {'Content-Type': 'application/json', 'User-Agent': 'PatrocleBot (patroclebot@strainu.ro)' }
		data = {"text": text}
		r = requests.post(url=self.url, headers=headers, data=json.dumps(data))
		if r.status_code != 200:
			pywikibot.error(f"Obtaining the {self.get_name()} from {self.url} "
							f"failed with code {r.status_code}")
			return 0, None
		try:
			resp = r.json()
			score = resp["score"]
			prediction = resp["wikicode"]
		except Exception as e:
			raise ValueError(f"Obtaining the {self.get_name()} failed with "
							 f"error {e}. URL was {self.url}")
		finally:
			r.close()
			return score, prediction

	@staticmethod
	def get_name() -> str:
		return "langid"