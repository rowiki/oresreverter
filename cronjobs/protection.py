#!/usr/bin/python3
# -*- coding: utf-8  -*-
import datetime
import re
from typing import Any

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import SingleSiteBot


def page_unprotected_generator():
    """
    Generator function to yield unprotected pages.
    """
    yield from pagegenerators.CategorizedPageGenerator(
        pywikibot.page.Category(pywikibot.Site(),
                                title="Categorie:Pagini neprotejate ce conțin formate de protejare"))

def page_protected_generator():
    """
    Generator function to yield pages needing protection.
    """
    yield from set(pagegenerators.LogeventsPageGenerator(logtype="protect", reverse=True, total=500))

class ProtectionBot(SingleSiteBot):
    """
    A bot to check and update page protections
    """

    def __init__(self, dry_run=False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #self.site = pywikibot.Site()
        self._dry_run = dry_run
        self.protection_levels = [ '', 'autoconfirmed', 'extendedconfirmed', 'templateeditor', 'sysop' ]
        self.template_regex = r'\{\{(?:[Tt]emplate:|[Ff]ormat:|)([Pp]p[^\|]*|[Pp]rotejat)([^\}]*)\}\}'
        self.regexes = [r'',
                        r'\{\{(?:[Tt]emplate:|[Ff]ormat:|)([Pp]p-semi[^\|]*|[Pp]rotejat)(|[^\}]*)\}\}',
                        r'\{\{(?:[Tt]emplate:|[Ff]ormat:|)([Pp]p-sporit|[Pp]p-extended|[Pp]rotejat)([^\}]*?)\}\}',
                        r'\{\{(?:[Tt]emplate:|[Ff]ormat:|)([Pp]p-format[^\|]*|[Pp]p-template[^\|]*|[Pp]rotejat)([^\}]*?)\}\}',
                        r'\{\{(?:[Tt]emplate:|[Ff]ormat:|)([Pp]p|[Pp]rotejat)(|[^\}]*)\}\}',
                        ]
        self.simple_template = '{{Protejat}}'
        self.small_template = '{{Protejat|small=yes}}'

    def treat(self, page: pywikibot.Page) -> None:
        if (not page.exists() or page.isRedirectPage() or
                page.namespace() in [2, 828] or page.namespace() % 2 == 1 or
                page.title().endswith('.js') or
                page.title().endswith('.css')):
            return

        protection = page.protection()
        for key in sorted(protection.keys()):
            # we only handle edit protections
            if key != 'edit':
                continue
            if protection[key][0] != self.protection_levels[0]:
                # some protection exists
                oldtext = text = page.get()
                expiry = datetime.datetime.now() + datetime.timedelta(days=30)
                if protection[key][1] != 'infinity':
                    expiry = datetime.datetime.strptime(protection[key][1], '%Y-%m-%dT%H:%M:%SZ')

                replacement = self.simple_template
                if expiry > datetime.datetime.now() + datetime.timedelta(days=7):
                    replacement = self.small_template

                pywikibot.output("" + page.title())
                entries = re.search(self.template_regex, text)
                if entries is not None:
                    #check if we need to update the template
                    idx = self.protection_levels.index(protection[key][0])
                    if re.search(self.regexes[idx], text) is None:
                        # add existing parameters to the new template
                        if entries.group(2) is not None:
                            replacement = self.simple_template[:-2] + entries.group(2) + '}}'
                        #replace the first occurrence
                        text, changes = re.subn(
                            f'({self.template_regex})', replacement, text)
                else:
                    #pywikibot.output("No template found, adding one to [[%s]].", page.title())
                    #pywikibot.output(protection[key][0])
                    #pywikibot.output(text[:100])
                    #add the template
                    if page.namespace() == 10:
                        #for template namespace, add noinclude
                        replacement = '<noinclude>' + replacement + '</noinclude>'
                    text = replacement + text

                #pywikibot.output(protection[key][0])
                pywikibot.showDiff(oldtext, text)
                if not self._dry_run:
                    page.put(text, summary="Actualizat formatul de protejare conform nivelului de protecție")


if __name__ == "__main__":
    bot = ProtectionBot(generator=page_protected_generator())
    bot.run()