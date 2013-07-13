import re

from lxml import html

from pelican import signals

from memorised.decorators import memorise

"""
nofollow plugin for pelican
================================

Adds rel=nofollow to urls that are not in the whitelist.

Requirements
------------
   easy_install lxml (yes, easy_install works better for lxml)

Settings
--------
To enable, add

    from pelican.plugins import nofollow
    PLUGINS = [nofollow]

    NOFOLLOW_WHITELIST = ['yoursite.com', 'partnersite.com']

to your settings.py.
"""


def initialize_settings(generator):
    if not generator.settings.has_key('NOFOLLOW_WHITELIST'):
        generator.settings['NOFOLLOW_WHITELIST'] = \
            [generator.settings['SITEURL']]
    if generator.settings['RELATIVE_URLS']:
        generator.settings['NOFOLLOW_WHITELIST'].append('^\.*/.*$')
    generator.settings['NOFOLLOW_WHITELIST'].append('^\|.*\|.*$')

    generator.settings['NOFOLLOW_REGEXP'] = []
    for expr in generator.settings['NOFOLLOW_WHITELIST']:
        generator.settings['NOFOLLOW_REGEXP'].append(re.compile(expr))


def article_update(generator, article):
    article_html = html.fromstring(article._content)
    changed = False
    for link in article_html.xpath('//a'):
        href = link.get('href')
        if not href:
            continue
        match = True
        for regexp in generator.settings['NOFOLLOW_REGEXP']:
            href = link.get('href')
            if regexp.match(href):
                match = False
                break
        if match:
            changed = True
            rel = link.get('rel')
            rel = "%s nofollow" if rel else "nofollow"
            link.set('rel', rel)

    if changed:
        article._content = html.tostring(article_html, encoding='unicode', method='xml')
        article._content = article._content.replace(u'\xa0', '&nbsp;')
    

def register():
    signals.article_generator_init.connect(initialize_settings)
    signals.article_update.connect(article_update)
