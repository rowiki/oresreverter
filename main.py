#!/usr/bin/python3
# -*- coding: utf-8  -*-
# type: ignore

import datetime
import pywikibot
from oresreverter.change import Change
from oresreverter.config import BotConfig
from oresreverter.recentchanges import recentchanges
import time

def notify_maintainer(user, exception):
	error = f"\n==Eroare in PatrocleBot==\n{str(exception)}--~~~~\n"
	try:
		page = pywikibot.Page(pywikibot.Site(), user, ns=3)
		text = page.get()
		text += error
		page.put(text, "Eroare")
		pywikibot.output(error)
	except:
		pywikibot.output(error)

def single_run():
	dry_run = False
	page="MediaWiki:Revertbot.json"
	model=None

	local_args = pywikibot.handle_args()
	for arg in local_args:
		# Handle args whether we are running in dry run mode
		if arg.startswith('-dry-run'):
			dry_run = True
		if arg.startswith('-cfg:'):
			page = arg.split(':', maxsplit=1)[1]
		if arg.startswith('-model:'):
			model = arg.split(':')[1]

	site = pywikibot.Site("ro", "wikipedia")
	site.login()
	processed_timestamp = None

	cfg = BotConfig(site, page=page, model_name=model, dry_run=dry_run)
	backoff_factor = 1
	min_backoff_factor = 1
	max_backoff_factor = int((cfg.rc_interval_max + cfg.rc_interval_min - 1) / cfg.rc_interval_min)

	pywikibot.output(f"Started bot with config {page}, model {cfg.model_name}")

	while True:
		try:
			changes = recentchanges(site,
									end=processed_timestamp,
									namespaces=cfg.namespaces,
									total=cfg.rc_limit,
									top_only=True,
									patrolled=False,
									reverse=False)

			count = 0
			for p in changes:
				if count == 0:
					processed_timestamp = pywikibot.Timestamp.fromISOformat(p.get('timestamp'))
					timediff = datetime.timedelta(seconds=1)
					processed_timestamp = processed_timestamp + timediff
				#pywikibot.output(p)
				change = Change(site, p, cfg)
				change.treat()
				count += 1

			if count == 0:
				if backoff_factor < max_backoff_factor:
					backoff_factor += 1
				processed_timestamp = pywikibot.Timestamp.utcnow()
			elif backoff_factor > min_backoff_factor:
				backoff_factor = int(backoff_factor / 2)
			backoff_time = backoff_factor * cfg.rc_interval_min
			print(f"Treated {count} pages. Now sleeping for {backoff_time}s, then starting from {processed_timestamp} UTC.", flush=True)
			time.sleep(backoff_time)
		except Exception as e:
			if dry_run:
				raise e
			else:
				notify_maintainer(cfg.maintainer, e)

if __name__ == "__main__":
	single_run()
