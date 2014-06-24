from pagetree.models import Hierarchy
from pagetree.reports import StandaloneReportColumn, PagetreeReport
from pagetree.tests.factories import PagetreeTestCase, UserFactory


class PagetreeReportColumnTest(PagetreeTestCase):

    def setUp(self):
        super(PagetreeReportColumnTest, self).setUp()

        self.column = StandaloneReportColumn('username', 'profile',
                                             'string', 'Username',
                                             lambda x: x.username)

    def test_identifier(self):
        self.assertEquals(self.column.identifier(), 'username')

    def test_metadata(self):
        key_row = ['', 'username', 'profile', 'string', 'Username']
        self.assertEquals(self.column.metadata(), key_row)

    def test_user_value(self):
        user = UserFactory()
        self.assertEquals(self.column.user_value(user), user.username)


class PagetreeReportTest(PagetreeTestCase):

    def setUp(self):
        super(PagetreeReportTest, self).setUp()
        self.report = PagetreeReport()
        self.user = UserFactory()

    def test_users(self):
        self.assertEquals(len(self.report.users()), 1)

    def test_standalone_columns(self):
        self.assertEquals(len(self.report.standalone_columns()), 0)

    def test_metadata_columns(self):
        hierarchies = Hierarchy.objects.all()
        self.assertEquals(len(hierarchies), 2)
        columns = self.report.metadata_columns(hierarchies)
        self.assertEquals(len(columns), 2)

    def test_metadata(self):
        hierarchies = Hierarchy.objects.all()
        rows = []
        for row in self.report.metadata(hierarchies):
            rows.append(row)
        self.assertEquals(len(rows), 4)

    def test_value_columns(self):
        hierarchies = Hierarchy.objects.all()
        columns = self.report.value_columns(hierarchies)
        self.assertEquals(len(columns), 2)

    def test_values(self):
        hierarchies = Hierarchy.objects.all()
        rows = []
        for row in self.report.values(hierarchies):
            rows.append(row)
        self.assertEquals(len(rows), 2)

        self.assertEquals(rows[1][0], self.user.username)
