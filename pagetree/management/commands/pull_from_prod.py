from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.conf import settings
from json import loads
from pagetree.models import Hierarchy
from restclient import GET
import os.path


class Command(BaseCommand):
    args = '<hierarchy name> (optional)'
    help = 'pull the pagetree data down from production'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            print("this should never be run on production")
            return
        if not hasattr(settings, 'PROD_BASE_URL'):
            print("you must set PROD_BASE_URL")
            return
        print("fetching content from prod...")
        url = settings.PROD_BASE_URL + "_pagetree/export/"
        if args:
            url = url + "?hierarchy=" + args[0]
        d = loads(GET(url))
        print("removing old pagetree hierarchy...")
        Hierarchy.objects.all().delete()
        print("importing the new one...")
        Hierarchy.from_dict(d)

        if not hasattr(settings, 'PROD_MEDIA_BASE_URL'):
            print("in order to pull down uploaded files,")
            print("you must set PROD_MEDIA_BASE_URL")

        print("pulling down uploaded files...")
        base_len = len(settings.PROD_MEDIA_BASE_URL)
        for upload in d.get('resources', []):
            relative_path = upload[base_len:]
            relative_dir = os.path.join(*os.path.split(relative_path)[:-1])
            full_dir = os.path.join(settings.MEDIA_ROOT, relative_dir)
            try:
                os.makedirs(full_dir)
            except OSError:
                pass
            with open(os.path.join(settings.MEDIA_ROOT,
                                   relative_path), "w") as f:
                print("  writing %s to %s" % (upload, relative_path))
                f.write(GET(upload))
        print("done")
