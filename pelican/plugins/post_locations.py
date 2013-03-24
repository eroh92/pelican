# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from operator import attrgetter
from collections import defaultdict

from pelican import signals, contents
from pelican.utils import slugify


class Country(contents.URLWrapper):
    def __init__(self, name, *args, **kwargs):
        name = name.strip()
        super(Country, self).__init__(name, *args, **kwargs)


class City(contents.URLWrapper):
    def __init__(self, name, *args, **kwargs):
        name = name.strip()
        city, country = name.split(',')
        self.city = city.strip()
        self.country = Country(country, *args, **kwargs)
        super(City, self).__init__(name, *args, **kwargs)
        self.slug = "%s/%s" % (slugify(self.city), slugify(self.country))


def init_locations(article_generator):
    article_generator.locations = defaultdict(list)
    article_generator.countries = \
        defaultdict(article_generator.locations.__copy__)


def parse_metadata(article_generator, metadata):
    if metadata.has_key('locations'):
        locations = []
        for location in metadata['locations'].split(';'):
            locations.append(City(location,
                                  settings=article_generator.settings))
        metadata['locations'] = locations


def add_locations_to_generator(article_generator):
    for article in article_generator.articles:
        if article.status == "published" and hasattr(article, 'locations'):
            for location in article.locations:
                article_generator.locations[location].append(article)
                article_generator.countries[location.country][location].append(article)


def generate_locations_pages(article_generator, write):
    location_template = article_generator.get_template('location')
    for location, articles in article_generator.locations.items():
        articles.sort(key=attrgetter('date'), reverse=True)
        dates = [article for article in article_generator.dates
                 if article in articles]
        write(location.save_as,
              location_template,
              article_generator.context,
              location=location,
              articles=articles,
              dates=dates,
              paginated={'articles': articles, 'dates': dates},
              page_name=location.page_name)


def register():
    signals.article_generator_init.connect(init_locations)
    signals.article_generate_context.connect(parse_metadata)
    signals.article_generator_finalized.connect(add_locations_to_generator)
    signals.article_generate_pages.connect(generate_locations_pages)
