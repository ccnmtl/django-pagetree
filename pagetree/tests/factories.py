from django.contrib.auth.models import User
from django.test.testcases import TestCase
from pagetree.models import Hierarchy, Section
import factory


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User
    username = factory.Sequence(lambda n: "user%03d" % n)
    password = factory.PostGenerationMethodCall('set_password', 'test')


class HierarchyFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Hierarchy
    name = "main"
    base_url = ""


class RootSectionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Section
    hierarchy = factory.SubFactory(HierarchyFactory)
    label = "Root"
    slug = ""


class ModuleFactory(object):
    def __init__(self, hname, base_url):
        hierarchy = HierarchyFactory(name=hname, base_url=base_url)
        root = hierarchy.get_root()
        root.add_child_section_from_dict(
            {'label': "One", 'slug': "one",
             'children': [{'label': "Three", 'slug': "introduction"}]})
        root.add_child_section_from_dict({'label': "Two", 'slug': "two"})

        blocks = [{'label': 'Welcome to your new Forest Site',
                   'css_extra': '',
                   'block_type': 'Test Block',
                   'body': 'You should now use the edit link to add content'}]
        root.add_child_section_from_dict({'label': 'Four', 'slug': 'four',
                                          'pageblocks': blocks})

        self.root = root


class PagetreeTestCase(TestCase):
    def setUp(self):
        super(PagetreeTestCase, self).setUp()

        ModuleFactory("one", "/pages/one/")
        ModuleFactory("two", "/pages/two/")

        self.hierarchy_one = Hierarchy.objects.get(name='one')
        self.hierarchy_two = Hierarchy.objects.get(name='two')
