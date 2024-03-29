""" run tests for pagetree

$ virtualenv ve
$ ./ve/bin/pip install Django==1.8
$ ./ve/bin/pip install -r test_reqs.txt
$ ./ve/bin/python runtests.py
"""


import django
from django.conf import settings
from django.core.management import call_command


def main():
    # Dynamically configure the Django settings with the minimum necessary to
    # get Django running tests
    settings.configure(
        MIDDLEWARE=(
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ),
        SECRET_KEY="Something Super Secret",
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [
                    # insert your TEMPLATE_DIRS here
                ],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.contrib.auth.context_processors.auth',
                        'django.template.context_processors.debug',
                        'django.template.context_processors.i18n',
                        'django.template.context_processors.media',
                        'django.template.context_processors.static',
                        'django.template.context_processors.tz',
                        'django.contrib.messages.context_processors.messages',
                    ],
                },
            },
        ],
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'pagetree',
            'django_jenkins',
            'markdownify.apps.MarkdownifyConfig',
        ),

        MARKDOWNIFY = {
            "default": {
                "WHITELIST_TAGS": [
                    'a',
                    'abbr',
                    'acronym',
                    'b',
                    'blockquote',
                    'em',
                    'i',
                    'li',
                    'ol',
                    'p',
                    'strong',
                    'ul'
                ]
            },
        },

        TEST_RUNNER='django.test.runner.DiscoverRunner',
        DEFAULT_AUTO_FIELD = 'django.db.models.AutoField',
        COVERAGE_EXCLUDES_FOLDERS=['migrations'],
        ROOT_URLCONF='pagetree.tests.urls',
        PAGEBLOCKS=['pagetree.TestBlock', ],

        PROJECT_APPS=[
            'pagetree',
        ],

        # Django replaces this, but it still wants it. *shrugs*
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
                'HOST': '',
                'PORT': '',
                'USER': '',
                'PASSWORD': '',
            }
        },
    )

    django.setup()

    # Fire off the tests
    call_command('migrate')
    call_command('test')


if __name__ == '__main__':
    main()
