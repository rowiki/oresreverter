#!/usr/bin/python3
# -*- coding: utf-8  -*-

import json
import pywikibot
import requests

from pywikibot.tools import is_ip_address

class RevertedUser:
	black_dot = "■"
	block_level = 5
	block_notify = "Wikipedia:Reclamații"
	block_message = "{{{{subst:Notificare blocare|{user}|2={{{{subst:evaluare automată|url_erori=Discuție Utilizator:PatrocleBot}}}}}}}}--~~~~"
	block_description = "Notificare pentru blocarea utilizatorului {user}"
	warn_message = "{{{{subst:au-vandalism{level}{article}|2={{{{subst:evaluare automată}}}} }}}}--~~~~"
	ip_advice = "{{{{subst:SharedIPAdvice}}}}"
	warn_description = "Avertizare de nivel {level} pentru vandalism la [[{article}]]"

	def __init__(self, username: str):
		self.username = username
		#TODO: dehardcode namespace
		self.userpage = f"Discuție_Utilizator:{self.username}"

	def get_last_warning_level(self) -> int:
		count = 0
		try:
			url = f"https://ro.wikipedia.org/w/api.php?action=parse&prop=sections&page={self.userpage}&format=json"
			r = requests.get(url)
			if r.status_code != 200:
				raise ValueError(f"Obtaining the last warning level failed with code {r.status_code}")
			ret = r.json()
			if "parse" not in ret or "sections" not in ret["parse"]:
				return 0
			sections = ret["parse"]["sections"]
			for s in range(len(sections) - 1, -1, -1):
				line = sections[s]["line"]
				loc = line.find(self.black_dot)
				if loc > -1:
					for idx in range(loc, loc+5):
						if line[idx] == self.black_dot:
							count += 1
					return count
		except Exception as e:
			print(e)
			count = 0
		return count

	def warn(self, level: int, article: str):
		article_template = ""
		if article is not None:
			article_template = "|" + article
		warn_message = self.warn_message.format(level=level, article=article_template)
		description = self.warn_description.format(level=level, article=article or "<articol necunoscut>")
		up = pywikibot.Page(pywikibot.Site(), self.userpage)
		text = ""
		if up.exists():
			text = up.get()
		text += "\n" + warn_message
		if is_ip_address(self.username):
			text += "\n" + ip_advice
		pywikibot.info(warn_message)
		pywikibot.info(description)
		up.put(text, summary=description)

	def report(self):
		warn_message = self.block_message.format(user=self.username)
		description = self.block_description.format(user=self.username)
		p = pywikibot.Page(pywikibot.Site(), self.block_notify)
		text = ""
		if p.exists():
			text = p.get()
		text += "\n" + warn_message
		pywikibot.info(warn_message)
		pywikibot.info(description)
		p.put(text, summary=description, botflag=False)

	def warn_or_report(self, article: str=None):
		level = 1 + self.get_last_warning_level()
		if level >= self.block_level:
			self.warn(self.block_level, article)
			self.report()
		else:
			self.warn(level, article)
