#!/usr/bin/python3
# -*- coding: utf-8  -*-

import pywikibot
import requests

class Change(object):
	def __init__(self, site, info, cfg):
		self._site = site
		self._revid = info['revid']
		self._title = info['title']
		if type(info['oresscores']) == dict:
			self._score = info['oresscores']['damaging']['true']
		else:
			self._score = None
		self._cfg = cfg

	def get_score(self):
		if not isinstance(self._revid, int):
			raise TypeError(f"revid must be an int, not {type(self.revid)}")

		if self._score is not None:
			return

		dbname = self._site.dbName()
		# https://ores.wikimedia.org/v3/scores/rowiki/14806453/damaging
		r = requests.get(f"https://ores.wikimedia.org/v3/scores/{dbname}/{self._revid}/damaging")
		if r.status_code != 200:
			raise ValueError(f"Obtaining the ORES score failed with code {r.status_code}")
		try:
			resp = r.json()
			self._score = resp[dbname]["scores"][str(self._revid)]["damaging"]["score"]["probability"]["true"]
		except Exception as e:
			raise ValueError(f"Obtaining the ORES score failed with error {e}. URL was https://ores.wikimedia.org/v3/scores/{dbname}/{self._revid}/damaging")
		finally:
			r.close()

	@property
	def score(self):
		if self._score is None:
			self.get_score()
		return self._score

	@property
	def revid(self):
		return self._revid

	@property
	def article(self):
		return pywikibot.Page(site, self._title)

	def treat(self):
		if self.score >= self._cfg.threshhold:
			print(self._title, self._revid)