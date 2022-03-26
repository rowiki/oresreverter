#!/usr/bin/python3
# -*- coding: utf-8  -*-

import json
import pywikibot
from .report import get_reporter

class BotConfig:
	def __init__(self, site, page="MediaWiki:Revertbot.json"):
		self.site = site
		self.page = page
		self.reporter = get_reporter()

		self.load_config()
		self.reporter.interval = int(self.report_interval)

	def __repr__(self) -> str:
		return str(self.__dict__)

	def load_config(self):
		page = pywikibot.Page(self.site, self.page)
		if not page.exists():
			raise Exception(f"Config page {self.page} does not exits.")

		data = json.loads(page.get())
		self.__dict__.update(data)