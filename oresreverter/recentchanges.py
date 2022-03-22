#!/usr/bin/python3
# -*- coding: utf-8  -*-

import pywikibot
from pywikibot.data import api
from typing import Optional, Union, List
		

# https://ro.wikipedia.org/w/api.php?action=query&format=json&list=recentchanges&rcnamespace=0%7C4%7C6%7C8%7C10&rcprop=title%7Ctimestamp%7Cids%7Coresscores%7Ctags%7Cpatrolled&rcshow=unpatrolled&rclimit=50&rctype=edit%7Cnew%7Ccategorize
def recentchanges(site, *,
                  start=None,
                  end=None,
                  reverse: bool = False,
                  namespaces=None,
                  changetype: Optional[str] = None,
                  minor: Optional[bool] = None,
                  bot: Optional[bool] = None,
                  anon: Optional[bool] = None,
                  redirect: Optional[bool] = None,
                  patrolled: Optional[bool] = None,
                  top_only: bool = False,
                  total: Optional[int] = None,
                  user: Union[str, List[str], None] = None,
                  excludeuser: Union[str, List[str], None] = None,
                  tag: Optional[str] = None):
        """Iterate recent changes.

        :see: https://www.mediawiki.org/wiki/API:RecentChanges

        :param start: Timestamp to start listing from
        :type start: pywikibot.Timestamp
        :param end: Timestamp to end listing at
        :type end: pywikibot.Timestamp
        :param reverse: if True, start with oldest changes (default: newest)
        :param namespaces: only iterate pages in these namespaces
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param changetype: only iterate changes of this type ("edit" for
            edits to existing pages, "new" for new pages, "log" for log
            entries)
        :param minor: if True, only list minor edits; if False, only list
            non-minor edits; if None, list all
        :param bot: if True, only list bot edits; if False, only list
            non-bot edits; if None, list all
        :param anon: if True, only list anon edits; if False, only list
            non-anon edits; if None, list all
        :param redirect: if True, only list edits to redirect pages; if
            False, only list edits to non-redirect pages; if None, list all
        :param patrolled: if True, only list patrolled edits; if False,
            only list non-patrolled edits; if None, list all
        :param top_only: if True, only list changes that are the latest
            revision (default False)
        :param user: if not None, only list edits by this user or users
        :param excludeuser: if not None, exclude edits by this user or users
        :param tag: a recent changes tag
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        #if start and end:
        #    site.assert_valid_iter_params('recentchanges', start, end, reverse)

        rcgen = site._generator(api.ListGenerator, type_arg='recentchanges',
                                rcprop='user|timestamp|title|ids'
                                       '|flags|tags|oresscores',
                                namespaces=namespaces,
                                total=total, rctoponly=top_only)
        if start is not None:
            rcgen.request['rcstart'] = start
        if end is not None:
            rcgen.request['rcend'] = end
        if reverse:
            rcgen.request['rcdir'] = 'newer'
        if changetype:
            rcgen.request['rctype'] = changetype
        filters = {'minor': minor,
                   'bot': bot,
                   'anon': anon,
                   'redirect': redirect,
                   }
        if patrolled is not None and (
                site.has_right('patrol') or site.has_right('patrolmarks')):
            rcgen.request['rcprop'] += ['patrolled']
            filters['patrolled'] = patrolled
        rcgen.request['rcshow'] = api.OptionSet(site, 'recentchanges', 'show',
                                                filters)

        if user:
            rcgen.request['rcuser'] = user

        if excludeuser:
            rcgen.request['rcexcludeuser'] = excludeuser
        rcgen.request['rctag'] = tag
        return rcgen

# testing
if __name__ == "__main__":
	site = pywikibot.Site("ro", "wikipedia")
	for p in recentchanges(site, namespaces=[0,4,6,8,10], total=5000, top_only=True, changetype="edit|new|categorize", patrolled=False, reverse=True):
		if type(p['oresscores']) == dict:
			score = p['oresscores']['damaging']['true']
			if score >= 0.909:
				pywikibot.output(f"{p}")