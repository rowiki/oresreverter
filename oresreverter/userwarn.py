#!/usr/bin/python3
# -*- coding: utf-8  -*-

import json
import pywikibot
import requests

class RevertedUser:
	black_dot = "■"
	block_level = 5
	block_notify = "Wikipedia:Afișierul administratorilor"
	block_message = "{{{{subst:Notificare blocare|{user}|2=Evaluare făcută automat. Dacă sunt erori, vă rugăm să le raportați [[Discuție Utilizator:PatrocleBot|aici]].}}}}"
	block_description = "Notificare pentru blocarea utilizatorului {user}"
	warn_message = "{{{{subst:au-vandalism{level}{article}}}}}"
	warn_description = "Avertizare de nivel {level} pentru vandalism în {article}"

	def __init__(self, username: str):
		self.username = username
		#TODO: dehardcode namespace
		self.userpage = f"Discuție_Utilizator:{self.username}"

	def get_last_warning_level(self) -> int:
		try:
			url = f"https://ro.wikipedia.org/w/api.php?action=parse&prop=sections&page={self.userpage}&format=json"
			print(url)
			r = requests.get(url)
			if r.status_code != 200:
				raise ValueError(f"Obtaining the last warning level failed with code {r.status_code}")
			sections = r.json()["parse"]["sections"]
			for s in range(len(sections) - 1, 0, -1):
				count = 0
				line = sections[s]["line"]
				loc = line.find(self.black_dot)
				if loc > -1:
					for idx in range(loc, loc+5):
						if line[idx] == self.black_dot:
							count += 1
					return count
		except Exception as e:
			print(e)
			return 0

	def warn(self, level: int, article: str):
		article_template = ""
		if article is not None:
			article_template = "|" + article
		warn_message = self.warn_message.format(level=level, article=article_template)
		description = self.warn_description.format(level=level, article=article or "Wikipedia")
		up = pywikibot.Page(pywikibot.Site(), self.userpage)
		text = up.get()
		text += "\n" + warn_message
		print(warn_message, description)
		up.put(text, description)

	def report(self):
		warn_message = self.block_message.format(user=self.username)
		description = self.block_description.format(user=self.username)
		p = pywikibot.Page(pywikibot.Site(), self.block_notify)
		text = p.get()
		text += "\n" + warn_message
		print(warn_message, description)
		p.put(text, description)

	def warn_or_report(self, article: str=None):
		level = 1 + self.get_last_warning_level()
		if level >= self.block_level:
			self.warn(self.block_level, article)
			self.report()
		else:
			self.warn(level, article)
