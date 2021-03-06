#!/usr/bin/python3
# -*- coding: utf-8  -*-

import datetime
import json
import pywikibot
from .report import get_reporter
from .changetrack import get_tracker

class BotConfig:
	def __init__(self, site, page="MediaWiki:Revertbot.json"):
		self.ores_threshold = 0.909 # TODO: get from API
		self.site = site
		self.page = page

		tzoffset = datetime.timedelta(minutes=site.siteinfo['timeoffset'])
		self.reporter = get_reporter(datetime.timezone(tzoffset))
		self.tracker = get_tracker(datetime.timezone(tzoffset))

		self.load_config()

	def __repr__(self) -> str:
		return str(self.__dict__)

	def load_config(self):
		page = pywikibot.Page(self.site, self.page)
		if not page.exists():
			raise Exception(f"Config page {self.page} does not exits.")

		data = json.loads(page.get())
		#don't go below the ores "very likely damaging" threshold
		if float(data["threshold"]) < self.ores_threshold:
			data["threshold"] = self.ores_threshold
		self.__dict__.update(data)
		self.reporter.interval = int(self.report_interval)
		self.tracker.timeout = int(self.article_follow_interval)