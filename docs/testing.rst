Testing
============

It can be useful to programmatically set up a pagetree site for
testing purposes. If you have custom pageblocks that rely on
JavaScript for essential functionality, you won't be able to test that
code with django's built-in testing features. You can use Selenium
with Behave or Lettuce to do this kind of testing. This page shows how
to mock a version of your pagetree site in code.  It can then be used
for Selenium tests or for Django-style unittests.


Here's an example of a factory that you can put alongside
``factory_boy`` factories::

  from pagetree.tests.factories import HierarchyFactory


  class CustomPagetreeModuleFactory(object):
      def __init__(self):
          hierarchy = HierarchyFactory(name='main', base_url='/pages/')
          root = hierarchy.get_root()
          root.add_child_section_from_dict({
              'label': 'Welcome to the Intro Page',
              'slug': 'intro',
              'children': [
                  {
                      'label': 'Step 1',
                      'slug': 'step-1',
                      'pageblocks': [{
                          'block_type': 'Text Block'
                      }]
                  },
                  {
                      'label': 'Step 2',
                      'slug': 'step-2',
                      'pageblocks': [{
                          'block_type': 'My Block Name'
                      }]
                  },
              ]
          })

          self.root = root

To instantiate a custom pageblock in this way, you set ``block_type``
to the custom pageblock's ``display_name`` property.

Then, if you're writing a behave test, you can call this factory in
``environment.py``::

  def before_all(context):
      CustomPagetreeModuleFactory()

And navigate the hierarchy in the feature file:

.. code-block:: gherkin

   Feature: Navigate the pagetree hierarchy
     Scenario: Access custom block on Step 2
       When I visit "/pages/"
       Then I see the text "Welcome to the Intro Page"

       When I click the next button
       Then I see the text "Step 1"

       When I click the next button
       Then I see the text "Step 2"
       Then I see the text "My Block Name"
