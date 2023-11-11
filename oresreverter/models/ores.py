#!/usr/bin/python3
# -*- coding: utf-8  -*-
from .base import ModelConfig
from typing import Tuple
import requests

class OresBaseConfig(ModelConfig):
	"""Configuration for the ORES model."""
	def __init__(self):
		self.url = "https://ores.wikimedia.org/v3/scores/{dbname}/{revid}/{type}"
		self.type = None
		self.docs = ":mw:ORES"

	def likely_bad(self, score:float) -> bool:
		return score >= self.cfg[self.type]['likely']

	def possibly_bad(self, score:float) -> bool:
		return score >= self.cfg[self.type]['possible']

	def likely_constructive(self, score:float) -> bool:
		return score <= self.cfg[self.type]['minimal']

	def get_score(self, lang: str, revid: int) -> float:
		score, _ = self.get_result(lang, revid)
		return score

	def get_result(self, lang: str, revid: int) -> Tuple[float, bool]:
		score = None
		prediction = False
		dbname = lang + "wiki"
		url = self.url.format(dbname=dbname, revid=revid, type=self.type)
		r = requests.get(url)
		if r.status_code != 200:
			raise ValueError(f"Obtaining the {self.get_name()} score for revision {revid} failed with code {r.status_code}")
		try:
			resp = r.json()
			score = resp[dbname]["scores"][str(revid)][self.type]["score"]["probability"]["true"]
			prediction = resp[dbname]["scores"][str(revid)][self.type]["score"]["prediction"]
		except Exception as e:
			raise ValueError(f"Obtaining the {self.get_name()} score for revision {revid} failed with error {e}. URL was {url}")
		finally:
			r.close()
			return score, prediction

class OresDamagingConfig(OresBaseConfig):
	def __init__(self):
		super(OresDamagingConfig, self).__init__()
		self.type = "damaging"

	@staticmethod
	def get_name() -> str:
		return "ores.damaging"

class OresGoodfaithConfig(OresBaseConfig):
	def __init__(self):
		super(OresGoodfaithConfig, self).__init__()
		self.type = "goodfaith"

	@staticmethod
	def get_name() -> str:
		return "ores.goodfaith"

class OresConfig(OresBaseConfig):
	def __init__(self):
		super(OresBaseConfig, self).__init__()
		self.type = ""
		self.gf = OresGoodfaithConfig()
		self.dmg = OresDamagingConfig()

	@staticmethod
	def get_name() -> str:
		return "ores"

	def likely_bad(self, score:float) -> bool:
		return self.dmg.likely_bad(score) and self.gf.likely_bad(score)

	def possibly_bad(self, score:float) -> bool:
		return (self.dmg.likely_bad(score) and self.gf.possibly_bad(score)) or \
			   (self.dmg.possibly_bad(score) and self.gf.likely_bad(score))

	def likely_constructive(self, score:float) -> bool:
		return self.dmg.likely_constructive(score) and self.gf.likely_constructive(score)

	def set_config(self, config: dict):
		self.dmg.set_config(config)
		self.gf.set_config(config)

	def get_result(self, lang: str, revid: int) -> Tuple[float, bool]:
		gf_score, gf_prediction = self.gf.get_result(lang, revid)
		dmg_score, dmg_prediction = self.dmg.get_result(lang, revid)
		score = dmg_score
		prediction = gf_prediction and dmg_prediction
		return score, prediction
