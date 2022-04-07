#!/usr/bin/python3
# -*- coding: utf-8  -*-

import pywikibot
import requests
from .userwarn import RevertedUser

class Change(object):
	def __init__(self, site, info, cfg):
		self._site = site
		self._revid = info['revid']
		self._title = info['title']
		self._article = pywikibot.Page(self._site, self._title)
		self._user = RevertedUser(info['user'])
		if type(info.get('oresscores')) == dict:
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
		return self._article

	def revert(self):
		user = self._user.username
		expl = f"Se revine automat asupra unei modificări distructive (scor [[:mw:ORES|ORES]]: {self.score}). Greșit? Raportați [[WP:AA|aici]]."
		try:
			self._cfg.tracker.add_change(self._title, user)
			self._site.loadrevisions(self.article, content=False, total=10)
			self._site.rollbackpage(self.article, user=user, summary=expl)
			self._user.warn_or_report(self._title)
		except Exception as e:
			pywikibot.output(f"Error rollbacking page: {e}")
			self._cfg.reporter.report_failed_revert()
		else:
			self._cfg.reporter.report_successful_revert()
			pywikibot.output(f"The edit(s) made in {self._title} by {user} was rollbacked")
		finally:
			pass #TODO maybe warn here?

	def treat(self):
		if self.score < self._cfg.threshold:
			if self.score >= self._cfg.ores_threshold:
				if self._cfg.tracker.tracked_change(self._title, self._user.username):
					self.revert()
				else:
					self._cfg.reporter.report_near_revert()
			else:
				self._cfg.reporter.report_no_revert()
			return
		self._cfg.load_config()
		if self._cfg.active:
			self.revert()
		else:
			pywikibot.output(f"Found revert candidate: [[{self._title}]]@{self._revid} (score={self.score})")
