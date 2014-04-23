import logging
import re

import flickr_api

from time import sleep
from httplib import BadStatusLine
from datetime import datetime
from functools import partial
from pelican import signals

logger = logging.getLogger(__name__)

"""
Flickr plugin for pelican
================================

Adds flickr set metadata to article objects.

Requirements
------------
    pip install flickr-api

Settings
--------
To enable, add

    from pelican.plugins import flickr
    PLUGINS = [flickr]

    FLICKR_KEY = 'XXXXX'
    FLICKR_SECRET = 'XXXXX'

to your settings.py.

To control the attributes of the photo objects, add the following

    FLICKR_EXTRA_PARAMS = {'extras': 'date_taken, geo, tags, o_dims, url_l'}

to your settings.py.

Add a flickr photoset id in the metadata of your article file:

    Flickrset: XXXX

If you leave out Date and Title from the article metadata, this plugin pulls
the title and date from the photoset.

Usage
-----
    <h1>Photo Album: {{ article.photoset.title }}</h1>
    <ul>
    {% for photo in article.photos %}
        <img height="{{ photo.height_l }}"
             width="{{ photo.width_l }}"
             src="{{ photo.url_l }}"
             alt="{{ photo.title }}"/>
        <span>{{ photo.title }}</span>
    {% endfor %}
    </ul>

"""

photo_cache = {}


def _get_photo(id, extra_params):
    logger.debug('lookup flicker photo #%s' % id)
    id = unicode(id)
    if not id in photo_cache:
        photo = flickr_api.Photo(id=id, **extra_params)
        photo_cache[id] = photo
    return photo_cache[str(id)]


def has_flickr_settings(generator):
    return 'FLICKR_SECRET' in generator.settings and \
        'FLICKR_KEY' in generator.settings


def initialize_flickr_api(generator):
    if has_flickr_settings(generator):
        flickr_api.set_keys(generator.settings['FLICKR_KEY'],
                            generator.settings['FLICKR_SECRET'])
        if not 'FLICKR_EXTRA_PARAMS' in generator.settings:
            generator.settings['FLICKR_EXTRA_PARAMS'] = \
                {'extras': 'url_l, url_m'}
        if not 'FLICKR_MAX_HEIGHT' in generator.settings:
            generator.settings['FLICKR_MAX_HEIGHT'] = 768
        if not 'FLICKR_MAX_WIDTH' in generator.settings:
            generator.settings['FLICKR_MAX_WIDTH'] = 1024
        if not 'FLICKR_THUMBNAIL_MAX_HEIGHT' in generator.settings:
            generator.settings['FLICKR_THUMBNAIL_MAX_HEIGHT'] = 480
        if not 'FLICKR_THUMBNAIL_MAX_WIDTH' in generator.settings:
            generator.settings['FLICKR_THUMBNAIL_MAX_WIDTH'] = 640


def _get_photoset_data(photoset_id, extra_params):
    photoset = flickr_api.Photoset(id=photoset_id)
    photoset.load()
    photos = photoset.getPhotos(**extra_params)
    for photo in photos:
        photo_cache[photo.id] = photo
    return (photoset, photos)


def add_flickr_metadata(generator, metadata):
    if has_flickr_settings(generator) and 'flickrset' in metadata:
        photoset, photos = \
            _get_photoset_data(metadata['flickrset'],
                               generator.settings['FLICKR_EXTRA_PARAMS'])
        metadata['photoset'] = photoset
        metadata['photos'] = photos
        if not 'title' in metadata:
            metadata['title'] = photoset.title
        if not 'thumbnail' in metadata:
            for photo in photos:
                if photo.isprimary == '1':
                    metadata['thumbnail'] = photo.url_l
        if not 'date' in metadata:
            metadata['date'] = \
                datetime.fromtimestamp(float(photoset.date_create))


flickr_re = re.compile(r"(<p>)?\|flickr:(?P<flickr_id>.*?)\|(</p>)?")


def _get_url(photo, max_height, max_width):
    for size, data in sorted(photo.getSizes().items(),
                             key=lambda x: int(x[1]['width']),
                             reverse=True):
        url = data['source']
        height = int(data['height'])
        width = int(data['width'])
        if (height <= max_height and
                width <= max_width):
            return (url, height, width)


def square_thumb_replace(photo, generator, *args, **kwargs):
    return photo.getSizes()['Large Square']['source']


def alt_thumb_replace(photo, generator, *args, **kwargs):
    return photo.title


def thumbnail_replace(photo, generator, *args, **kwargs):
    photo_url, height, width = _get_url(
        photo,
        generator.settings['FLICKR_THUMBNAIL_MAX_HEIGHT'],
        generator.settings['FLICKR_THUMBNAIL_MAX_WIDTH'])
    return photo_url


def insert_image(photo, article, generator, *args, **kwargs):
    try:
        template = generator.get_template('flickr_image')
        photo_url, height, width = _get_url(
            photo,
            generator.settings['FLICKR_MAX_HEIGHT'],
            generator.settings['FLICKR_MAX_WIDTH'])
        return template.render(photo=photo,
                               photo_url=photo_url,
                               photo_height=height,
                               photo_width=width,
                               article=article,
                               **generator.settings)
    except BadStatusLine:
        print 'Flickr is dogging it... sleeping for 5 seconds.'
        sleep(5)
        insert_image(photo, article, generator, *args, **kwargs)


def flickr_replace(generator, article, replacer_func):
    def replacer(m, generator, article, replacer_func):
        photo = _get_photo(m.group('flickr_id'),
                           generator.settings['FLICKR_EXTRA_PARAMS'])
        return replacer_func(photo=photo,
                             article=article,
                             generator=generator)
    return partial(replacer,
                   generator=generator,
                   article=article,
                   replacer_func=replacer_func)


def article_update(generator, article):
    flickr_var = '|flickr_images|'
    if (has_flickr_settings(generator)
            and hasattr(article, 'flickrset')
            and article._content.find(flickr_var) > -1):
        template = generator.get_template('flickr_images')
        output = template.render(article=article, **article.settings)
        article._content = article._content.replace(flickr_var, output)
    if has_flickr_settings(generator):
        if hasattr(article, 'thumbnail'):
            article.square_thumbnail = article.thumbnail
            alt = article.thumbnail
            thumbnail = \
                flickr_re.sub(flickr_replace(generator,
                                             article,
                                             thumbnail_replace),
                              article.thumbnail)
            square_thumbnail = \
                flickr_re.sub(flickr_replace(generator,
                                             article,
                                             square_thumb_replace),
                              article.square_thumbnail)
            alt = \
                flickr_re.sub(flickr_replace(generator,
                                             article,
                                             alt_thumb_replace),
                              alt)
            if alt:
                article.thumbnail_alt = alt
            else:
                article.thumbnail_alt = None
            article.thumbnail = thumbnail
            article.square_thumbnail = square_thumbnail
            article.metadata['thumbnail'] = thumbnail
        new_content = \
            flickr_re.sub(flickr_replace(generator, article, insert_image),
                          article._content)
        if new_content is not article._content:
            article._content = new_content


def register():
    signals.article_generator_init.connect(initialize_flickr_api)
    signals.article_update.connect(article_update)
    signals.article_generate_context.connect(add_flickr_metadata)
