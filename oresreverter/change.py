#!/usr/bin/python3
# -*- coding: utf-8  -*-
# type: ignore

from .config import BotConfig
import pywikibot
import requests
from .userwarn import RevertedUser

class Change(object):
	def __init__(self, site, info, cfg: BotConfig):
		self._site = site
		self._revid = info['revid']
		self._title = info['title']
		self._article = pywikibot.Page(self._site, self._title)
		self._user = RevertedUser(info['user'], cfg.article_follow_interval)
		self._score = None
		self._cfg = cfg
		self._model = cfg.model

	def get_score(self):
		if not isinstance(self._revid, int):
			raise TypeError(f"revid must be an int, not {type(self.revid)}")

		if self._score is not None:
			return

		self._score = self._model.get_score(lang=self._site.lang, revid=self._revid)

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
		if not self._cfg.active:
			pywikibot.output(f"Found revert candidate: [[{self._title}]]@{self._revid} ({self._model.get_name()} score={self.score})")
			#pywikibot.output(f"|-\n| [[Special:Diff/{self._revid}|{self._title}]] || || ")
			return

		user = self._user.username
		docs_link = f"[[{self._model.get_docs()}|{self._model.get_name()}]]"
		expl = f"Se revine automat asupra unei modificări distructive (scor {docs_link}: {self.score}). Greșit? Raportați [[WP:AA|aici]]."
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
			pywikibot.output(f"Found patrol candidate: [[{self._title}]]@{self._revid} ({self._model.get_name()} score={self.score})")
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
		#pywikibot.output(self._title, self.revid, self.score, flush=True)
		# failed to get score from the model
		if self.score == 0:
			return
		if self.score >= self._cfg.threshold:
			self._cfg.load_config()
			self._site.login()
			self.revert()
		else:
			if self._model.likely_bad(self.score):
				if self._cfg.tracker.tracked_change(self._title, self._user.username):
					self.revert()
				else:
					self._cfg.reporter.report_near_revert()	
			elif self._model.possibly_bad(self.score):
				self._cfg.reporter.report_near_revert()
			elif self._model.likely_constructive(self.score):
				self.patrol()
			else:
				self._cfg.reporter.report_no_revert()
			return
		
