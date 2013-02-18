""" run tests for pagetree

$ virtualenv ve
$ ./ve/bin/pip install -q -e .
$ ./ve/bin/pip install test_reqs/sorl-3.1.tar.gz
$ ./ve/bin/pip install test_reqs/django-pageblocks-0.5.9.tar.gz
$ ./ve/bin/python runtests.py
"""


from django.conf import settings
from django.core.management import call_command


def main():
    # Dynamically configure the Django settings with the minimum necessary to
    # get Django running tests
    settings.configure(
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'pagetree',
            'pageblocks',
            'django_nose',
            'django.contrib.markup',
        ),
        TEST_RUNNER = 'django_nose.NoseTestSuiteRunner',

        NOSE_ARGS = [
            '--with-coverage',
            '--cover-package=pagetree',
            ],

        ROOT_URLCONF = [],
        PAGEBLOCKS = ['pageblocks.TextBlock',
              'pageblocks.HTMLBlock',
              'pageblocks.PullQuoteBlock',
              'pageblocks.ImageBlock',
              'pageblocks.ImagePullQuoteBlock',
              'quizblock.Quiz',
              'careermapblock.CareerMap',
              'fridgeblock.FridgeBlock',
              ],
        SOUTH_TESTS_MIGRATE=False,

        # Django replaces this, but it still wants it. *shrugs*
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
                'HOST': '',
                'PORT': '',
                'USER': '',
                'PASSWORD': '',
                }
            }
    )

    # Fire off the tests
    call_command('test', 'pagetree')

if __name__ == '__main__':
    main()
