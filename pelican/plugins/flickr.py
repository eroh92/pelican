import flickr_api

from datetime import datetime
from pelican import signals

from memorised.decorators import memorise

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

def has_flickr_settings(generator):
    return generator.settings.has_key('FLICKR_SECRET') and \
            generator.settings.has_key('FLICKR_KEY')


def initialize_flickr_api(generator):
    if has_flickr_settings(generator):
        flickr_api.set_keys(generator.settings['FLICKR_KEY'],
                            generator.settings['FLICKR_SECRET'])
        if not generator.settings.has_key('FLICKR_EXTRA_PARAMS'):
            generator.settings['FLICKR_EXTRA_PARAMS'] = \
                {'extras': 'url_l, url_m'}


def _get_photoset_data(photoset_id, extra_params):
    photoset = flickr_api.Photoset(id=photoset_id)
    photoset.load()
    photos = photoset.getPhotos(**extra_params)
    return (photoset, photos)


def add_flickr_metadata(generator, metadata):
    if has_flickr_settings(generator) and metadata.has_key('flickrset'):
        photoset, photos = \
            _get_photoset_data(metadata['flickrset'],
                               generator.settings['FLICKR_EXTRA_PARAMS'])
        metadata['photoset'] = photoset
        metadata['photos'] = photos
        if not metadata.has_key('title'):
            metadata['title'] = photoset.title
        if not metadata.has_key('thumbnail'):
            for photo in photos:
                if photo.isprimary == '1':
                    metadata['thumbnail'] = photo.url_l
        if not metadata.has_key('date'):
            metadata['date'] = \
                datetime.fromtimestamp(float(photoset.date_create))


def article_update(generator, article):
    flickr_var = '|flickr_images|'  
  
    if (has_flickr_settings(generator)
            and hasattr(article, 'flickrset')
            and article._content.find(flickr_var) > -1):
        template = generator.get_template('flickr')
        output = template.render(article=article, **article.settings)
        article._content = article._content.replace(flickr_var, output)
        article.get_content.func.im_self.cache.clear()


def register():
    signals.article_generator_init.connect(initialize_flickr_api)
    signals.article_update.connect(article_update)
    signals.article_generate_context.connect(add_flickr_metadata)
