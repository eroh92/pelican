# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import collections
import os.path
import math

from datetime import datetime
from logging import warning, info
from codecs import open

from pelican import signals, contents
from pelican.plugins.post_locations import Location

TXT_HEADER = """{0}/index.html
"""

XML_HEADER = """<?xml version="1.0" encoding="utf-8"?>
<urlset xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 "
"http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd"
xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""

XML_URL = """
<url>
<loc>{0}/{1}</loc>
<lastmod>{2}</lastmod>
<changefreq>{3}</changefreq>
<priority>{4}</priority>
</url>
"""

XML_FOOTER = """
</urlset>
"""


def format_date(date):
    if date.tzinfo:
        tz = date.strftime('%s')
        tz = tz[:-2] + ':' + tz[-2:]
    else:
        tz = "-00:00"
    return date.strftime("%Y-%m-%dT%H:%M:%S") + tz


class SitemapGenerator(object):

    def __init__(self, context, settings, path, theme, output_path, *null):

        self.output_path = output_path
        self.context = context
        self.now = datetime.now()
        self.siteurl = settings.get('SITEURL')

        self.format = 'xml'

        self.changefreqs = {
            'articles': 'monthly',
            'indexes': 'daily',
            'pages': 'monthly'
        }

        self.priorities = {
            'articles': 0.5,
            'indexes': 0.5,
            'pages': 0.5
        }

        config = settings.get('SITEMAP', {})

        if not isinstance(config, dict):
            warning("sitemap plugin: the SITEMAP setting must be a dict")
        else:
            fmt = config.get('format')
            pris = config.get('priorities')
            chfreqs = config.get('changefreqs')

            if fmt not in ('xml', 'txt'):
                warning("sitemap plugin: SITEMAP['format'] must be `txt' or "
                        "`xml'")
                warning("sitemap plugin: Setting SITEMAP['format'] on `xml'")
            elif fmt == 'txt':
                self.format = fmt
                return

            valid_keys = ('articles', 'indexes', 'pages')
            valid_chfreqs = ('always', 'hourly', 'daily', 'weekly', 'monthly',
                             'yearly', 'never')

            if isinstance(pris, dict):
                # We use items for Py3k compat. .iteritems() otherwise
                for k, v in pris.items():
                    if k in valid_keys and not isinstance(v, (int, float)):
                        default = self.priorities[k]
                        warning("sitemap plugin: priorities must be numbers")
                        warning("sitemap plugin: setting SITEMAP['priorities']"
                                "['{0}'] on {1}".format(k, default))
                        pris[k] = default
                self.priorities.update(pris)
            elif pris is not None:
                warning("sitemap plugin: SITEMAP['priorities'] must be a dict")
                warning("sitemap plugin: using the default values")

            if isinstance(chfreqs, dict):
                # .items() for py3k compat.
                for k, v in chfreqs.items():
                    if k in valid_keys and v not in valid_chfreqs:
                        default = self.changefreqs[k]
                        warning("sitemap plugin: invalid "
                                "changefreq `{0}'".format(v))
                        warning("sitemap plugin: setting "
                                "SITEMAP['changefreqs']"
                                "['{0}'] on '{1}'".format(k, default))
                        chfreqs[k] = default
                self.changefreqs.update(chfreqs)
            elif chfreqs is not None:
                warning("sitemap plugin: SITEMAP['changefreqs'] "
                        "must be a dict")
                warning("sitemap plugin: using the default values")

    def write_url(self, page, fd):

        if getattr(page, 'status', 'published') != 'published':
            return

        page_path = os.path.join(self.output_path, page.url)
        if not os.path.exists(page_path):
            return

        lastmod = format_date(getattr(page, 'date', self.now))

        if isinstance(page, contents.Article):
            pri = self.priorities['articles']
            chfreq = self.changefreqs['articles']
        elif isinstance(page, Location) and self.priorities['locations'] \
                and self.changefreqs['locations']:
            pri = self.priorities['locations']
            chfreq = self.changefreqs['locations']
        elif isinstance(page, contents.Page):
            pri = self.priorities['pages']
            chfreq = self.changefreqs['pages']
        else:
            pri = self.priorities['indexes']
            chfreq = self.changefreqs['indexes']

        if self.format == 'xml':
            fd.write(XML_URL.format(self.siteurl, page.url,
                                    lastmod, chfreq, pri))
            if hasattr(page, 'article_count'):
                paginate = collections.namedtuple('p', ['number'])
                pages = int(math.ceil(
                    page.article_count /
                    float(self.context['DEFAULT_PAGINATION'])))
                if pages > 1:
                    for p in range(2, pages + 1):
                        paginate.number = p
                        fd.write(XML_URL.format(
                            self.siteurl,
                            page.paginated_url(paginate),
                            lastmod,
                            chfreq,
                            pri))
        else:
            fd.write(self.siteurl + '/' + page.url + '\n')

    def generate_output(self, writer):
        path = os.path.join(self.output_path,
                            'sitemap.{0}'.format(self.format))

        for category, articles in self.context['categories']:
            category.article_count = len(articles)
        for tag, articles in self.context['tags']:
            tag.article_count = len(articles)
        for author, articles in self.context['authors']:
            author.article_count = len(articles)

        pages = self.context['pages'] + self.context['articles'] \
            + [c for (c, a) in self.context['categories']] \
            + [t for (t, a) in self.context['tags']] \
            + [a for (a, b) in self.context['authors']]

        if 'location_articles' in self.context:
            for location, articles in self.context['location_articles']:
                location.article_count = len(articles)
            pages += [l for (l, b) in self.context['location_articles']]

        for article in self.context['articles']:
            pages += article.translations

        info('writing {0}'.format(path))

        FakePage = collections.namedtuple('FakePage',
                                          ['status',
                                           'date',
                                           'url'])

        with open(path, 'w', encoding='utf-8') as fd:

            if self.format == 'xml':
                fd.write(XML_HEADER)
            else:
                fd.write(TXT_HEADER.format(self.siteurl))

            for standard_page_url in ['']:
                fake = FakePage(status='published',
                                date=self.now,
                                url=standard_page_url)
                self.write_url(fake, fd)

            for page in pages:
                self.write_url(page, fd)

            if 'index' in self.context['PAGINATED_DIRECT_TEMPLATES']:
                page_count = int(math.ceil(
                    len(self.context['articles']) /
                    float(self.context['DEFAULT_PAGINATION'])))
                if page_count > 1:
                    pattern = self.context['INDEX_PAGINATED_URL']
                    for p in range(2, page_count + 1):
                        fake = FakePage(status='published',
                                        date=self.now,
                                        url=pattern.format(page=p))
                        self.write_url(fake, fd)

            if self.format == 'xml':
                fd.write(XML_FOOTER)


def get_generators(generators):
    return SitemapGenerator


def register():
    signals.get_generators.connect(get_generators)
