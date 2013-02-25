from django.test import TestCase
from check.models import *
from checkmarc.settings import PROJECT_DIR
from pymarc import MARCReader

class CheckTestCase(TestCase):
    def setUp(self):

        self.record = [r for r in
            MARCReader(open(PROJECT_DIR + "/../test-helpers/files/books.mrc"),
            to_unicode=True)][0]

        self.fieldNotEqual = Check(field=u"245",operator=u"nq", values=u"Some unlikely book title")
        self.subfieldEquals = Check(field=u"245", subfield=u"a", operator=u"eq", values=u"The alpha masters :")
        self.indicatorIn = Check(field=u"245", indicator=u"1", operator=u"cn", values=u"0,4")
        self.subfieldExists = Check(field=u"245", subfield=u"a", operator=u"ex")
        self.subfieldDoesntExist = Check(field=u"245", subfield=u"q", operator=u"nx")


    def test_unicode_display(self):
        self.assertEqual(self.fieldNotEqual.__unicode__(),
            u"245 is not Some unlikely book title",
            self.fieldNotEqual.__unicode__() + u"is not the expected result")
        self.assertEqual(self.subfieldEquals.__unicode__(),
            u"245 a is The alpha masters :",
            u"Unicode representation does not match expected result")
        self.assertEqual(self.indicatorIn.__unicode__(),
            u"245 indicator1 contains any of the following 0,4",
            self.indicatorIn.__unicode__() + u" is not the expected result")
        self.assertEqual(self.subfieldExists.__unicode__(),
            u"245 a exists",
            self.subfieldExists.__unicode__() + u" is not expected result")
        self.assertEqual(self.subfieldDoesntExist.__unicode__(),
            u"245 q does not exist",
            self.subfieldDoesntExist.__unicode__() + u"is not the expected result")

    def test_run_check(self):
        self.assertTrue(self.subfieldEquals.run(self.record),
            u"Returning false on " + self.record['245']['a'] + u" == " + self.subfieldEquals.values)
        self.assertTrue(self.fieldNotEqual.run(self.record),
            u"Returning false on " + self.record['245'].value() + u" != " + self.fieldNotEqual.values)
        self.assertTrue(self.indicatorIn.run(self.record),
            u"Returning false on " + self.record['245'].indicator1 + u" is in " + self.indicatorIn.values)
        self.assertTrue(self.subfieldExists.run(self.record),
            u"Returns that existing field does not exist ")
        self.assertTrue(self.subfieldDoesntExist.run(self.record),
            u"Returns that non-existent subfield does exist")

    def test_helper_methods(self):
        self.assertTrue(self.indicatorIn._indicator(), u"Returns False that indicator exists and subfield doesn't")
        self.assertFalse(self.indicatorIn._indicator(),u"Returns True that indicator exists or subfield doesnt")


    def tearDown(self):
        self.record = None
        self.fieldNotEqual = None
        self.subfieldEquals = None
        self.indicatorIn = None
        self.subfieldExists = None
