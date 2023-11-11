#!/usr/bin/python3
# -*- coding: utf-8  -*-

import datetime
import json
import oresreverter.models as models
import pywikibot
from .report import get_reporter
from .changetrack import get_tracker


NAME_SEP = "."

class BotConfig:
	def __init__(self, site, page, model_name, dry_run=False):
		self.site = site
		self.page = page
		self.active = not dry_run
		self.model_name = model_name

		tzoffset = datetime.timedelta(minutes=site.siteinfo['timeoffset'])
		self.reporter = get_reporter(timezone=datetime.timezone(tzoffset), dry_run=dry_run)
		self.tracker = get_tracker(timezone=datetime.timezone(tzoffset))

		self.load_config()


	def __repr__(self) -> str:
		return str(self.__dict__)

	def load_config(self):
		page = pywikibot.Page(self.site, self.page)
		if not page.exists():
			raise Exception(f"Config page {self.page} does not exist.")

		data = json.loads(page.get())
		#override config with local parameters
		if self.model_name is not None:
			data["model_name"] = self.model_name
		# Dry-run mode
		if not self.active:
			data["active"] = False
		self.__dict__.update(data)

		if "report_interval" in data:
			self.reporter.interval = int(self.report_interval) # type: ignore
		if "article_follow_interval" in data:
			self.tracker.timeout = int(self.article_follow_interval) # type: ignore
		if "model_name" in data:
			self.model = models.get_model(data["model_name"])
		if self.model is None:
			self.model = models.get_model()
		self.model_name = self.model.get_name()
		if self.model_name in data:
			self.model.set_config(data.get(self.model_name))
		elif self.model_name.find(NAME_SEP) > -1:
			self.model.set_config(data.get(self.model_name.split(NAME_SEP)[0]))

		
		# don't go below the model's threshold
		if not self.model.likely_bad(float(data["threshold"])):
			raise Exception(f"Threshold {data['threshold']} is too low.")
