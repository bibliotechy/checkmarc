from django.test import TestCase
from check.models import *
from checkmarc.settings import PROJECT_DIR
from pymarc import MARCReader

class CheckTestCase(TestCase):
    def setUp(self):

        self.record = [r for r in
            MARCReader(open(PROJECT_DIR + "/../test-helpers/files/books.mrc"),
            to_unicode=True)][0]

        self.leaderPositionEquals = Check(leader=5, operator=u"eq", values=u"c")
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
            self.subfieldDoesntExist.__unicode__() + u" is not the expected result")
        self.assertEqual(self.leaderPositionEquals.__unicode__(),
            u"Leader position 5 is c",
            self.leaderPositionEquals.__unicode__() + u" is not the expected result" )

    def test_run_check(self):
        """
        Testing that a Check object performs comparison correctly
        and returns the expected truthy or falsy value .
        """
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
        self.assertTrue(self.leaderPositionEquals.run(self.record),
            u"Returns False on " + self.record.leader[self.leaderPositionEquals.leader] +
            u" == " + self.leaderPositionEquals.values)

    def test_helper_methods(self):
        #Leader helper
        self.assertTrue(self.leaderPositionEquals._leader(),
            u"Returns False that leader exists when it is not present")
        self.assertFalse(self.fieldNotEqual._leader(),
            u"Returns True that leader exists when it is not present")
        #Field helper
        self.assertTrue(self.fieldNotEqual._field(),
            u"Returns False that field exists and/or subfield and/or indicator do not")
        self.assertFalse(self.subfieldEquals._field(),
            u"Returns True that field doesnt exist and/or subfield or indicator does ")
        #Subfield helper
        self.assertTrue(self.subfieldEquals._subfield(),
            u"Returns False that subfield exists when it is present")
        self.assertFalse(self.indicatorIn._subfield(),
            u"Returns True that subfield exists when it is not present")
        #indicator helper
        self.assertTrue(self.indicatorIn._indicator(),
            u"Returns False that indicator exists and subfield doesn't")
        self.assertFalse(self.subfieldEquals._indicator(),
            u"Returns True that indicator exists or subfield doesn't")

        self.assertTrue(hasattr(self.leaderPositionEquals._select_operation_function(), "__call__" ),
            u"Should return a function that is callable")



    def tearDown(self):
        self.record = None
        self.fieldNotEqual = None
        self.subfieldEquals = None
        self.indicatorIn = None
        self.subfieldExists = None
