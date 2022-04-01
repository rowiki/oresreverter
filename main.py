#!/usr/bin/python3
# -*- coding: utf-8  -*-

import datetime
import pywikibot
from oresreverter.change import Change
from oresreverter.config import BotConfig
from oresreverter.recentchanges import recentchanges
import time

def notify_maintainer(user, exception):
	error = f"\n==Eroare in PatrocleBot==\n{str(exception)}--~~~~\n"
	try:
		page = pywikibot.Page(pywikibot.Site(), user, ns=2)
		text = page.get()
		text += error
		page.put(text, "Eroare")
	except:
		pywikibot.output(error)

def single_run():
	site = pywikibot.Site("ro", "wikipedia")
	site.login()
	cfg = BotConfig(site)
	processed_timestamp = None
	backoff_factor = 1
	min_backoff_factor = 1
	max_backoff_factor = int((cfg.rc_interval_max + cfg.rc_interval_min - 1) / cfg.rc_interval_min)

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
				change = Change(site, p, cfg)
				change.treat()
				#pywikibot.output(p)
				count += 1

			if count == 0:
				if backoff_factor < max_backoff_factor:
					backoff_factor += 1
				processed_timestamp = pywikibot.Timestamp.utcnow()
			elif backoff_factor > min_backoff_factor:
				backoff_factor = int(backoff_factor / 2)
			backoff_time = backoff_factor * cfg.rc_interval_min
			print(f"Treated {count} pages. Now sleeping for {backoff_time}s, then starting from {processed_timestamp}.", flush=True)
			time.sleep(backoff_time)
		except Exception as e:
			notify_maintainer(cfg.maintainer, e)

if __name__ == "__main__":
	single_run()