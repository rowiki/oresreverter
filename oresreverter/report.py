#!/usr/bin/python3
# -*- coding: utf-8  -*-

import json
import pywikibot
from pywikibot import config
from datetime import datetime
from datetime import timezone

class BotReporter(object):
	"""A singleton alowing the bot to write reports"""

	def __init__(self, report_interval_s, tz):
		if config.family in config.usernames:
			family = config.usernames[config.family]
		else:
			family = config.usernames['*']

		if config.mylang in family:
			self.user = family[config.mylang]
		else:
			self.user = family['*']
		self.interval_s = report_interval_s
		self.tz = tz
		self.dry_run = False
		self.reset_report()

	def reset_report(self):
		self.start = datetime.now(self.tz)
		self.end = None
		self.revert_success = 0
		self.revert_fail = 0
		self.patrol_success = 0
		self.patrol_fail = 0
		self.near_revert = 0
		self.all_changes = 0
		self.bpv_added = 0
		self.bpv_removed = 0

	def report_successful_revert(self):
		self.revert_success += 1
		self.all_changes += 1

		self.maybe_publish_report()

	def report_failed_revert(self):
		self.revert_fail += 1
		self.all_changes += 1

		self.maybe_publish_report()

	def report_successful_patrol(self):
		self.patrol_success += 1
		self.all_changes += 1

		self.maybe_publish_report()

	def report_failed_patrol(self):
		self.patrol_fail += 1
		self.all_changes += 1

		self.maybe_publish_report()

	def report_near_revert(self):
		self.near_revert += 1
		self.all_changes += 1

		self.maybe_publish_report()

	def report_successful_blp_add(self):
		self.bpv_added += 1
		#self.all_changes += 1

		self.maybe_publish_report()

	def report_successful_blp_removal(self):
		self.bpv_removed += 1
		#self.all_changes += 1

		self.maybe_publish_report()

	def report_no_revert(self):
		self.all_changes += 1
		# This is by far the most common case, so no report publishing here; wait for an error instead

	def build_report(self) -> str:
		txt = "\n== Raport din {{subst:CURRENTYEAR}}-{{subst:CURRENTMONTH}}-{{subst:CURRENTDAY2}} {{subst:LOCALTIME}} ==\n"
		txt += f"*''Interval'': {self.start} - {self.end}\n"
		txt += f"*''Editări anulate'': {self.revert_success} ({{{{dim|{self.revert_success * 100 / self.all_changes}|%}}}})\n"
		txt += f"*''Editări cu probleme neanulate'': {self.near_revert} ({{{{dim|{self.near_revert * 100 / self.all_changes}|%}}}})\n"
		txt += f"*''Anulări eșuate'': {self.revert_fail} ({{{{dim|{self.revert_fail * 100 / self.all_changes}|%}}}})\n"
		txt += f"*''Editări patrulate'': {self.patrol_success} ({{{{dim|{self.patrol_success * 100 / self.all_changes}|%}}}})\n"
		txt += f"*''Patrulări eșuate'': {self.patrol_fail} ({{{{dim|{self.patrol_fail * 100 / self.all_changes}|%}}}})\n"
		txt += f"*''Schimbări verificate'': {self.all_changes} ({{{{dim|100|%}}}})\n"
		txt += f"*''Formate BPV adăugate'': {self.bpv_added}\n"
		txt += "~~~~\n"
		
		return txt

	def maybe_publish_report(self):
		self.end = datetime.now(self.tz)
		tdelta = self.end - self.start
		
		if self.dry_run and self.all_changes % 100 == 0:
			self.publish_cli_report()
		else:
			if tdelta.total_seconds() < self.interval_s:
				return
			self.publish_wiki_report()

	def publish_cli_report(self):
		pywikibot.output(self.build_report())

	def publish_wiki_report(self) -> None:
		try:
			page = pywikibot.Page(pywikibot.Site(), f"Utilizator:{self.user}/Rapoarte")
			txt = page.get()
			txt += self.build_report()
			page.put(txt, "Adaug un raport de rulare")
			self.reset_report()
		except Exception as e:
			print("Exception while saving report", e)
			return

	@property
	def interval(self):
		return self.interval_s

	@interval.setter
	def interval(self, report_interval_s):
		self.interval_s = report_interval_s

reporter = BotReporter(7 * 24 * 3600, timezone.utc)

def get_reporter(timezone=None, dry_run=False) -> BotReporter:
	if timezone:
		reporter.tz = timezone
		reporter.dry_run = dry_run
		reporter.reset_report()
	return reporter
