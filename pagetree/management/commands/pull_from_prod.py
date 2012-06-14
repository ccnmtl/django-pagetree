from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.simplejson import loads
from pagetree.models import Hierarchy
from restclient import GET


class Command(BaseCommand):
    args = '<hierarchy name> (optional)'
    help = 'pull the pagetree data down from production'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            print "this should never be run on production"
            return
        print "fetching content from prod..."
        url = settings.PROD_BASE_URL + "_pagetree/export/"
        if args:
            url = url + "?hierarchy=" + args[0]
        d = loads(GET(url))
        print "removing old pagetree hierarchy..."
        Hierarchy.objects.all().delete()
        print "importing the new one..."
        Hierarchy.from_dict(d)
        print "done"
