# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from blinker import signal

initialized = signal('pelican_initialized')
finalized = signal('pelican_finalized')
article_update = signal('article_update')
article_generate_preread = signal('article_generate_preread')
generator_init = signal('generator_init')
article_generate_context = signal('article_generate_context')
article_generator_init = signal('article_generator_init')
article_generator_finalized = signal('article_generate_finalized')
article_generate_pages = signal('article_generate_pages')
article_generate_feeds = signal('article_generate_feeds')
get_generators = signal('get_generators')
pages_generate_context = signal('pages_generate_context')
pages_generator_init = signal('pages_generator_init')
content_object_init = signal('content_object_init')
