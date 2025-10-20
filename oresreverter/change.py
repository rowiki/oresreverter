#!/usr/bin/python3
# -*- coding: utf-8  -*-
# type: ignore
import time
from contextlib import suppress
from threading import Thread

import mwparserfromhell
import requests
from cronjobs.blp import add_blp

import pywikibot
from pywikibot.exceptions import NoPageError
from .config import BotConfig
from .models.langid import LangIdConfig
from .userwarn import RevertedUser


def item_is_in_list(statement_list: list, itemlist: list[str]) -> bool:
	"""Verify if statement list contains at least one item from the itemlist.

param statement_list: Statement list
param itemlist: List of values (string)
return: Whether the item matches
"""
	for seq in statement_list or []:
		with suppress(AttributeError):  # Ignore NoneType error
			isinlist = seq.getTarget().getID()
			if isinlist in itemlist:
				return True
	return False


class Change(object):
	def __init__(self, site, info, cfg: BotConfig):
		self._site = site
		self._revid = info['revid']
		self._title = info['title']
		self._type = info['type']
		self._patrolled = info.get('patrolled')
		self._article = pywikibot.Page(self._site, self._title)
		self._user = RevertedUser(info['user'], cfg.tracker)
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

	def tag_for_speedy_deletion(self, tag: str, reason: str) -> None:
		if len(self.article.contributors()) == 1:
			text = f"{tag}\n{self.article.text}"
			expl = (f"Cerere de ștergere rapidă a unei pagini pentru "
					f"{reason}. Greșit? Raportați [P:AA|aici]].")
			self.article.put(text, summary=expl)
			pywikibot.output(f"Speedy deletion tag added to {self._title}.")

	def revert(self):
		if not self._cfg.enabled_tools['revert']:
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
			import traceback
			print(traceback.format_exc())
			self._cfg.reporter.report_failed_revert()
			self.tag_for_speedy_deletion("{{șr-g3-vandalism}}",
										 f"vandalism (scor [[{self._model.get_docs()}|{self._model.get_name()}]]: {self.score})")
		else:
			self._cfg.reporter.report_successful_revert()
			pywikibot.output(f"The edit(s) made in {self._title} by {user} was rollbacked.")
		finally:
			pass #TODO maybe warn here?

	def patrol(self) -> None:
		if not self._cfg.enabled_tools['patrol']:
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

	def work_on_blps(self) -> None:
		if self._type != 'new':
			return
		if not self._cfg.enabled_tools['blp_add']:
			pywikibot.output(f"Found BLP candidate: [[{self._title}]]@{self._revid}")
			return

		thread = Thread(target=self.check_blps)
		thread.start()

	def check_blps(self) -> None:
		#pywikibot.output(f"Working on blp in " + self._title)
		pywikibot.sleep(5 * 60) # wait 5 minutes before adding BLP
		#pywikibot.output(f"Working on blp {self._title} after sleep")
		if not self._article.exists():
			return
		try:
			item = self._article.data_item()
		except NoPageError:
			return
		# humans
		if (item is not None and item.get() and
			    item_is_in_list(item.claims.get('P31'), ['Q5'])):
			pywikibot.output(self._title + " is human...")
			if 'P569' in item.claims and 'P570' not in item.claims:
				#pywikibot.output(item.claims)
				add_blp(self._article.toggleTalkPage())
				self._cfg.reporter.report_successful_blp_add()

	def work_on_new_articles(self) -> None:
		if self._type != 'new':
			return
		if not self._cfg.enabled_tools['new_article_watch']:
			pywikibot.output(f"Found new article candidate: [[{self._title}]]@{self._revid}")
			return
		self.check_language()

	def check_language(self) -> None:
		langid = LangIdConfig()
		text = self._article.text
		wikicode = mwparserfromhell.parse(text)
		score, prediction = langid.get_result(wikicode.strip_code())
		if prediction != self._site.lang:
			print(f"New article {self._title} is in language {prediction} (score {score})")
			if score >= langid.threshold:
				self.tag_for_speedy_deletion("{{șr|Articol în altă limbă "
										 "decât româna}}", "limbă greșită")

	def treat(self) -> None:
		if not self._cfg.active:
			pywikibot.output(f"Dry run mode: skipping {self._title} @ {self._revid}")
			return
		# First, run the maintenance scripts
		self.work_on_blps()

		if self._patrolled is not None:
			#pywikibot.output(f"Skipping patrolled change: {self._title} @ {self._revid}")
			return
		#pywikibot.output(self._title, self.revid, self.score, flush=True)
		# failed to get score from the model
		if self.score == 0:
			self.work_on_new_articles() # one of the reason for score 0 could be new article
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
