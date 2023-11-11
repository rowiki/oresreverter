#!/usr/bin/python3
# -*- coding: utf-8  -*-
# type: ignore

from oresreverter.config import BotConfig
import pywikibot
import requests
from .userwarn import RevertedUser

class Change(object):
	def __init__(self, site, info, cfg: BotConfig):
		self._site = site
		self._revid = info['revid']
		self._title = info['title']
		self._article = pywikibot.Page(self._site, self._title)
		self._user = RevertedUser(info['user'])
		if type(info.get('oresscores')) == dict:
			self._score = info['oresscores']['damaging']['true']
		else:
			self._score = None
		if type(info.get('oresscores')) == dict:
			self._gf_score = info['oresscores']['goodfaith']['true']
		else:
			self._gf_score = None
		self._cfg = cfg

	def get_score(self):
		if not isinstance(self._revid, int):
			raise TypeError(f"revid must be an int, not {type(self.revid)}")

		if self._score is not None and self._gf_score is not None:
			return

		dbname = self._site.dbName()
		# https://ores.wikimedia.org/v3/scores/rowiki/14806453/damaging
		r = requests.get(f"https://ores.wikimedia.org/v3/scores/{dbname}/{self._revid}")
		if r.status_code != 200:
			raise ValueError(f"Obtaining the ORES score for revision {self._revid} failed with code {r.status_code}")
		try:
			resp = r.json()
			self._score = resp[dbname]["scores"][str(self._revid)]["damaging"]["score"]["probability"]["true"]
			self._gf_score = resp[dbname]["scores"][str(self._revid)]["goodfaith"]["score"]["probability"]["true"]
		except Exception as e:
			raise ValueError(f"Obtaining the ORES score failed with error {e}. URL was https://ores.wikimedia.org/v3/scores/{dbname}/{self._revid}")
		finally:
			r.close()

	@property
	def score(self):
		if self._score is None:
			self.get_score()
		return self._score

	@property
	def gf_score(self):
		if self._gf_score is None:
			self.get_score()
		return self._gf_score

	@property
	def revid(self):
		return self._revid

	@property
	def article(self):
		return self._article

	def likely_damaging(self):
		return self.score >= self._cfg.ores['damaging']['likely']

	def possibly_damaging(self):
		return self.score >= self._cfg.ores['damaging']['possible']

	def likely_constructive(self):
		return self.score <= self._cfg.ores['damaging']['minimal']

	def likely_badfaith(self):
		return self.gf_score <= self._cfg.ores['goodfaith']['likely']

	def possibly_badfaith(self):
		return self.gf_score <= self._cfg.ores['goodfaith']['possible']

	def likely_goodfaith(self):
		return self.gf_score >= self._cfg.ores['goodfaith']['minimal']

	def revert(self):
		if not self._cfg.active:
			pywikibot.output(f"Found revert candidate: [[{self._title}]]@{self._revid} (score={self.score}/gf={self.gf_score})")
			return
		user = self._user.username
		expl = f"Se revine automat asupra unei modificări distructive (scoruri [[:mw:ORES|ORES]]: {self.score}/{self.gf_score}). Greșit? Raportați [[WP:AA|aici]]."
		try:
			self._cfg.tracker.add_change(self._title, user)
			self._site.loadrevisions(self.article, content=False, total=10)
			self._site.rollbackpage(self.article, user=user, summary=expl)
			self._user.warn_or_report(self._title)
		except Exception as e:
			pywikibot.output(f"Error rollbacking page {self._title}: {e}")
			self._cfg.reporter.report_failed_revert()
		else:
			self._cfg.reporter.report_successful_revert()
			pywikibot.output(f"The edit(s) made in {self._title} by {user} was rollbacked.")
		finally:
			pass #TODO maybe warn here?

	def patrol(self) -> None:
		if not self._cfg.active:
			pywikibot.output(f"Found patrol candidate: [[{self._title}]]@{self._revid} (score={self.score}/gf={self.gf_score})")
			return
		try:
			list(self._site.patrol(revid=self._revid))
		except Exception as e:
			pywikibot.output(f"Error patrolling page {self._title}@{self._revid}: {e}")
			self._cfg.reporter.report_failed_patrol()
		else:
			self._cfg.reporter.report_successful_patrol()
			pywikibot.output(f"The edit(s) made in {self._title} by {self._user.username} was patrolled.")

	def treat(self) -> None:
		print(self._title, self.revid, self.score, self.gf_score, flush=True)
		if self.score >= self._cfg.threshold:
			self._cfg.load_config()
			self._site.login()
			self.revert()
		else:
			if self.likely_damaging():
				if self._cfg.tracker.tracked_change(self._title, self._user.username) or self.likely_badfaith():
					self.revert()
				elif self.possibly_badfaith():
					self._cfg.reporter.report_near_revert()
			elif self.possibly_damaging() and self.likely_badfaith():
				self._cfg.reporter.report_near_revert()
			elif self.likely_constructive() and self.likely_goodfaith():
				self.patrol()
			else:
				self._cfg.reporter.report_no_revert()
			return
		
