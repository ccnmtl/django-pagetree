from __future__ import unicode_literals

import abc
from six import add_metaclass

from django.contrib.auth.models import User
from django.apps import apps
from django.contrib.contenttypes.models import ContentType


@add_metaclass(abc.ABCMeta)
class ReportableInterface(object):
    """ Abstract base class for a reportable interface that can be added to
        a given pageblock to support dynamic discovery of reporting data

        To use:
        1. implement a custom ReportColumn for your block/user data
        2. implement the report_metadata and report_values on your block
        3. register as part of the ReportableInterface
           ReportableInterface.register()
    """

    @abc.abstractmethod
    def report_metadata(self):
        """ Return an array of implemented ReportColumns
        """
        return

    @abc.abstractmethod
    def report_values(self):
        """ Return an array of implemented ReportColumns
        """
        return


@add_metaclass(abc.ABCMeta)
class ReportColumnInterface(object):

    @abc.abstractmethod
    def identifier(self):
        """ Unique column identifier, returns a spaceless, lower-case string
        """
        return

    @abc.abstractmethod
    def metadata(self):
        """ Return an array of metadata information about this column
            Used in the report's "key" file

            return [hierarchy id, itemIdentifier, category, itemType, itemText,
                answerIdentifier, answerText]
        """
        return

    @abc.abstractmethod
    def user_value(self, user):
        """ Return the user value associated with this column """
        return


class StandaloneReportColumn(ReportColumnInterface):
    """ A generic report column with no pageblock/hierarchy association
        Small pieces of information like username, user profile information or
        percent complete are good candidates for a StandaloneReportColumn.
        The user value specification is handled by a passed in value function
    """

    def __init__(self, name, group, value_type, description, value_func):
        self.name = name
        self.group = group
        self.value_type = value_type
        self.description = description
        self.value_func = value_func

    def identifier(self):
        return self.name

    def metadata(self):
        # hierarchy is n/a
        return ["", self.name, self.group, self.value_type, self.description]

    def user_value(self, user):
        return self.value_func(user)


class PagetreeReport(object):

    def get_reportable_content_types(self):
        types = []
        hierarchy = apps.get_model('pagetree', 'hierarchy')
        for block in hierarchy.available_pageblocks():
            if issubclass(block, ReportableInterface):
                types.append(ContentType.objects.get_for_model(block))

        return types

    def __init__(self):
        self.types = self.get_reportable_content_types()

    def users(self):
        return User.objects.all()

    def standalone_columns(self):
        """ Return an array of columns with no pagegblock/hierarchy association
            example:
            return [StandaloneReportColumn('username', 'profile', 'string',
                                           'Unique Username',
                                           lambda x: x.username)]

            empty array returned by default
        """
        return []

    def metadata_columns(self, hierarchies):
        """ Iterate pageblocks in order, collect metadata columns """
        columns = self.standalone_columns()
        for hierarchy in hierarchies:
            for section in hierarchy.get_root().get_descendants():
                for p in section.pageblock_set.filter(
                        content_type__in=self.types):
                    columns += p.block().report_metadata()
        return columns

    def value_columns(self, hierarchies):
        """ Iterate pageblocks in order, collect value columns """
        columns = self.standalone_columns()
        for hierarchy in hierarchies:
            for section in hierarchy.get_root().get_descendants():
                for p in section.pageblock_set.filter(
                        content_type__in=self.types):
                    columns += p.block().report_values()
        return columns

    def value_headers(self, columns):
        headers = []
        for column in columns:
            headers += [column.identifier()]
        return headers

    def metadata(self, hierarchies):
        """
            A "key" for all questions and answers in the system.
            * One row for short/long text questions
            * Multiple rows for single/multiple-choice questions.
            Each question/answer pair should get its own  row
        """
        yield ['hierarchy', 'itemIdentifier', 'exercise type',
               'itemType', 'itemText', 'answerIdentifier', 'answerText']
        yield ''

        for column in self.metadata_columns(hierarchies):
            yield column.metadata()

    def values(self, hierarchies):
        """
        All system results
        * One or more column for each question in system.
            ** 1 column for short/long text. label = itemIdentifier from key
            ** 1 column for single choice. label = itemIdentifier from key
            ** n columns for multiple choice: 1 column for each possible answer
               *** column labeled as itemIdentifer_answer.id

            * One row for each user in the system.
                1. username
                2 - n: answers
                    * short/long text. text value
                    * single choice. answer.id
                    * multiple choice.
                        ** answer id is listed in each question/answer
                        column the user selected
                    * Unanswered fields represented as an empty cell
        """
        columns = self.value_columns(hierarchies)

        yield self.value_headers(columns)

        for user in self.users():
            row = []
            for column in columns:
                row.append(column.user_value(user))
            yield row
