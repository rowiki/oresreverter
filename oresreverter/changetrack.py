#!/usr/bin/python3
# -*- coding: utf-8  -*-

import json
import pywikibot
from pywikibot import config
from datetime import datetime
from datetime import timezone

class ChangeTracker:
	timeout: int = 120
	changelist = {}
	
	def __init__(self, tz, timeout_s: int):
		self.timeout = timeout_s
		self.tz = tz

	def add_change(self, page, user):
		now = datetime.now(self.tz)
		self.changelist[page][user] = now

	def tracked_change(self, page, user):
		now = datetime.now(self.tz)
		self.cleanup_list(now)
		if page not in self.changelist:
			return False
		if user not in self.changelist[page]:
			return False
		tdelta = now - self.changelist[page][user]
		if tdelta.total_seconds <= self.timeout:
			return True
		else:
			return False

	def cleanup_list(self, now):
		for page in self.changelist:
			for user in self.changelist[page]:
				tdelta = now - self.changelist[page][user]
				if tdelta.total_seconds > self.timeout:
					del self.changelist[page][user]
					if len(self.changelist[page]) == 0:
						del self.changelist[page]



tracker = ChangeTracker(timezone.utc, 120)

def get_tracker(timezone=None, timeout_s=120):
	tracker.timeout = timeout_s
	if timezone:
		tracker.tz = timezone
		tracker.cleanup_list(datetime.now(tracker.tz))
	return tracker