from pelican import signals

"""
Author metadata plugin for Pelican
================================

Adds additional metadata to author objects.

Settings
--------
To enable, add

    from pelican.plugins import author_metadata
    PLUGINS = [author_metadata]

    AUTHOR_METADATA = {'Jon Doe': {'first_name': 'Jon',
                                   'last_name': 'Doe',
                                   'twitter': '@jd'}}

to your settings.py.

Usage
-----
    <p>By {{ author }}. Follow on twitter {{ author.twitter }}.</p>

"""


def add_author_metadata(generator):
    if generator.settings.has_key('AUTHOR_METADATA'):
        metadata = generator.settings['AUTHOR_METADATA']
        for author in generator.authors:
            author[0].__dict__.update(metadata.get(author[0].name, {}))


def register():
    signals.article_generator_finalized.connect(add_author_metadata)
