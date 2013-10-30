""" run tests for pagetree

$ virtualenv ve
$ ./ve/bin/pip install -r test_reqs.txt
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
            'django_nose',
            'django_markwhat',
            'django_jenkins',
        ),
        TEST_RUNNER = 'django_nose.NoseTestSuiteRunner',

        NOSE_ARGS = [
            '--with-coverage',
            '--cover-package=pagetree',
        ],
        COVERAGE_EXCLUDES_FOLDERS = ['migrations'],
        ROOT_URLCONF = [],
        PAGEBLOCKS = ['pagetree.TestBlock', ],
        SOUTH_TESTS_MIGRATE=False,

        JENKINS_TASKS = (
            'django_jenkins.tasks.with_coverage',
            'django_jenkins.tasks.django_tests',
        ),
        PROJECT_APPS = [
            'pagetree',
        ],
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
        },
    )

    # Fire off the tests
    call_command('test')
    call_command('jenkins')

if __name__ == '__main__':
    main()
