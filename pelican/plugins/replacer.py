import re

from lxml import html

from pelican import signals

from memorised.decorators import memorise

"""
replacer plugin for pelican
================================

Adds rel=nofollow to urls that are not in the whitelist.

Requirements
------------
   easy_install lxml (yes, easy_install works better for lxml)

Settings
--------
To enable, add

    from pelican.plugins import replacer
    PLUGINS = [replacer]

    REPLACE = [('<p>TITLE', '<p class="title"><h3>Title</h3>), ..]

to your settings.py.
"""

def article_update(generator, article):
    if generator.settings.has_key('REPLACE'):
        content = article._content
        for old, new in generator.settings['REPLACE']:
            if type(old) is re._pattern_type:
                content = old.sub(new, content)
            else:
                content = content.replace(old, new)

        article._content = content
        article.get_content.func.im_self.cache.clear()
    

def register():
    signals.article_update.connect(article_update)
