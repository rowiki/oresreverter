#!/usr/bin/python3
# -*- coding: utf-8  -*-

from typing import Tuple
import pywikibot
from .base import ModelConfig
from  . import all_subclasses


class AllModelsConfig(ModelConfig):
	def __init__(self) -> None:
		# at this point in the function, `self` does not have a name and is removed from the list
		self.models = [x for x in all_subclasses(ModelConfig) if x.get_name() != None and x != self.__class__]
		self.threshold = 0.909 # TODO
		self.docs = "Utilizator:PatrocleBot"
		self.latest_model = self.__class__ # what model score we choose to return

	@staticmethod
	def get_name() -> str:
		return "multi-model"

	def likely_bad(self, score:float) -> bool:
		return self.latest_model.likely_bad(score)

	def possibly_bad(self, score:float) -> bool:
		return self.latest_model.possibly_bad(score)

	def likely_constructive(self, score:float) -> bool:
		return self.latest_model.likely_constructive(score)

	def get_name() -> str:
		return self.latest_model.get_name()

	def get_docs(self) -> str:
		return self.latest_model.get_docs()

	def get_score(self, lang: str, revid: int) -> float:
		score, _ = self.get_result(lang, revid)
		return score

	def get_result(self, lang: str, revid: int) -> Tuple[float, bool]:
		max_score = 0
		max_prediction = False
		results = {"revid": revid}
		try:
			for model in self.models:
				score, prediction = model.get_result(lang, revid)
				name = model.get_name()
				results[name + "_score"] = score
				results[name + "_prediction"] = prediction
				if score > max_score:
					max_score = score
					max_prediction = prediction
					self.latest_model = model
		except Exception as e:
			pywikibot.output(e)
		finally:
			pywikibot.output(",".join([str(x) for x in results.values()]))
			return max_score, max_prediction