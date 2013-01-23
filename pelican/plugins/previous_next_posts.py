from pelican import signals

"""
Previous and next posts plugin for Pelican
================================

Adds next_post and previous_post variables to article's context

Settings
--------
To enable, add

    from pelican.plugins import previous_next_posts
    PLUGINS = [previous_next_posts]

to your settings.py.

Usage
-----
    {% if article.previous_post %}
        <a href="{{ article.previous_post.url }}">Previous</a>
    {% endif %}
    {% if article.next_post %}
        <a href="{{ article.next_post.url }}">Next</a>
    {% endif %}


"""


def add_previous_next_posts(generator):
    for i, article in enumerate(generator.articles):
        if i > 0:
            article.next_post = generator.articles[i - 1]
        if i < len(generator.articles) - 1:
            article.previous_post = generator.articles[i + 1]


def register():
    signals.article_generator_finalized.connect(add_previous_next_posts)
