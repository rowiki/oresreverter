#!/usr/bin/python3
# -*- coding: utf-8  -*-
import re
import datetime
from typing import Any

import pywikibot
from pywikibot import textlib
from pywikibot.bot import SingleSiteBot
from pywikibot.data import sparql


def blp_remove_generator():
    """
    Generator function to yield recent deaths.
    """
    date_since = (pywikibot.Timestamp.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    query = f"""SELECT ?item WHERE {{
  ?item wdt:P31 wd:Q5;
    wdt:P570 ?dod.
  FILTER(?dod > "{date_since}T00:00:00Z"^^xsd:dateTime)
  FILTER(?dod < (NOW()))
  FILTER(EXISTS {{
    ?article schema:about ?item;
      schema:inLanguage "ro".
  }})
}}
"""
    #print(query)
    pattern = re.compile("Q\d+")
    site = pywikibot.Site().data_repository()
    dependencies = {'endpoint': 'https://query-main.wikidata.org/sparql',
                    'entity_url': 'https://www.wikidata.org/entity', 'repo': None}
    query_object = sparql.SparqlQuery(**dependencies)
    for elem in query_object.select(query):
        qid = pattern.search(elem['item']).group(0)
        yield pywikibot.ItemPage(site, qid)


def check_yes(value: str) -> bool:
    """
    Check if the text contains a positive response.
    Returns True if 'yes' or 'da' is found, otherwise False.
    """
    value = value.lower()
    return any(yes in value for yes in ["yes", "da"])


def get_blp(text: str):
    """
    Extract the BPV values from the given text.
    If no BPV is found, False is returned.
    """
    templates = textlib.extract_templates_and_params(text)

    for template in templates:
        if template[0].lower() in "bpv":
            return "{{" + template[0] + "}}"
        elif template[0].lower().startswith("proiect"):
            params = template[1]
            print("template:", template)
            print("params:", params)
            for param in params:
                name = param.strip().lower()
                if name in {"bpv", "living", "în viață"} and check_yes(params[param]):
                        return "\\|" + param + "=" + params[param]
    return None

def add_blp(talk_page: pywikibot.Page) -> None:
    """
    Add the BPV template to the talk page if it does not exist.
    """
    text = ""
    if talk_page.exists():
        text = talk_page.get() or ""
    blp = get_blp(text)
    if blp:
        print(f"BPV already exists: {blp}")
        return
    else:
        print("No BPV found, adding.")
        new_text = "{{bpv}}\n" + text
        pywikibot.showDiff(text, new_text, context=1)
        talk_page.put(new_text, summary="Adăugat formatul BPV pentru un articol recent creat despre o persoană în viață.")


class BLPBot(SingleSiteBot):
    def __init__(self, cronjob, dry_run=None, site=pywikibot.Site("wikidata", "wikidata"), generator=None):
        super(SingleSiteBot, self).__init__(
            generator=generator, site=site)
        self._cronjob = cronjob
        self._dry_run = dry_run
        self._site = site
        self.last_run = 0

    def setup(self) -> None:
        # reset generator for new run
        self.generator_completed = False
        generator_func = globals().get(f"{self._cronjob}_generator")
        self.generator = generator_func()

    def treat(self, item: Any) -> None:
        sitelink = item.getSitelink('rowiki', True)
        tp = pywikibot.Page(pywikibot.Site(), sitelink).toggleTalkPage()
        if not tp.exists():
            print(f"Talk page {tp.title()} does not exist, skipping.")
            return
        print(f"Recent death page: {tp.title()}")
        text = tp.get() or ""
        blp = get_blp(text)
        if blp:
            print(f"BPV found: {blp}")
            new_text = re.sub(blp, "", text)
            pywikibot.showDiff(text, new_text, context=1)
            if not self._dry_run:
                tp.put(new_text, summary="Scot formatul BPV pentru o persoană recent decedată.")
        else:
            print("No BPV found.")

if __name__ == "__main__":
    bot = BLPBot(generator=blp_remove_generator())
    bot.run()

