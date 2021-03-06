# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from operator import attrgetter
from collections import defaultdict

from pelican import signals, contents
from pelican.utils import slugify


class Location(contents.URLWrapper):
    def __init__(self, name, *args, **kwargs):
        locations = [loc.strip() for loc in name.split(',')]
        super(Location, self).__init__(locations.pop(0), *args, **kwargs)
        if len(locations) > 0:
            self.parent = make_location(', '.join(locations),
                                        child=self, *args, **kwargs)
        self.slug = self._location_slug
        self.children = {}

    def __len__(self):
        return len(self.children)

    def __getitem__(self, key):
        return self.children[key]

    def __setitem__(self, key, value):
        self.children[key] = value

    @property
    def has_parent(self):
        return hasattr(self, 'parent')

    @property
    def _location_slug(self):
        if self.has_parent:
            return '%s/%s' % (self.parent._location_slug, slugify(self.name))
        else:
            return slugify(self.name)

    @property
    def full_name(self):
        if self.has_parent:
            return '%s, %s' % (self.name, self.parent.full_name)
        else:
            return self.name

    @property
    def all_location_names(self):
        return [loc.name for loc in self.all_locations]

    @property
    def all_locations(self):
        if self.has_parent:
            locations = self.parent.all_locations
            locations.append(self)
            return locations
        else:
            return [self]


def _format_name(name):
    return ', '.join([loc.strip() for loc in name.split(',')])

location_storage = {}


def make_location(name, child=None, *args, **kwargs):
    name = _format_name(name)
    if not name in location_storage:
        location = Location(name, *args, **kwargs)
        location_storage[name] = location
    location = location_storage[name]
    if child is not None:
        location[child.name] = child
    return location


def init_locations(article_generator):
    article_generator.locations = defaultdict(set)
    article_generator.location_hierarchy = {}
    article_generator.all_locations = set()
    article_generator.location_articles = []


def parse_metadata(article_generator, metadata):
    if 'locations' in metadata:
        locations = []
        for location in metadata['locations'].split(';'):
            locations.append(make_location(
                location, settings=article_generator.settings))
        metadata['locations'] = locations


def add_locations_to_generator(article_generator):
    articles_by_location = defaultdict(set)
    for article in article_generator.articles:
        if article.status == "published" and hasattr(article, 'locations'):
            for locations in article.locations:
                for location in locations.all_locations:
                    article_generator.locations[location].add(article)
                    article_generator.all_locations.add(location)
                    articles_by_location[location].add(article)
                    if not location.has_parent:
                        article_generator.location_hierarchy[location.name] = \
                            location
    for location, articles in articles_by_location.items():
        article_generator.location_articles.append(
            (location, list(articles)))
    article_generator.context['locations'] = \
        article_generator.location_hierarchy
    article_generator.context['all_locations'] = \
        article_generator.all_locations
    article_generator.context['location_articles'] = \
        article_generator.location_articles

    for article in article_generator.articles:
        if article.status == "published" and hasattr(article, "locations"):
            related_by_location = defaultdict(set)
            for locations in article.locations:
                for location in locations.all_locations:
                    related_by_location[location].update(
                        article_generator.locations[location])
            article.related_by_location = related_by_location


def generate_locations_pages(article_generator, write):
    location_template = article_generator.get_template('location')
    for location, articles in article_generator.locations.items():
        articles = sorted(articles, key=attrgetter('date'), reverse=True)
        dates = [article for article in article_generator.dates
                 if article in articles]
        write(location.save_as,
              location_template,
              article_generator.context,
              location=location,
              urlwrapper=location,
              articles=articles,
              dates=dates,
              paginated={'articles': articles, 'dates': dates},
              page_name=location.page_name)


def register():
    signals.article_generator_init.connect(init_locations)
    signals.article_generate_context.connect(parse_metadata)
    signals.article_generator_finalized.connect(add_locations_to_generator)
    signals.article_generate_pages.connect(generate_locations_pages)
