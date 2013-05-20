from django.test import TestCase
from check.models import *
from checkmarc.settings import PROJECT_DIR
from pymarc import MARCReader
from django.test import client

class CheckTestCase(TestCase):
    def setUp(self):

        user = User.objects.create_user("tester", "testing@test.com", "tester")
        user.save()
        self.c = client.Client()

        self.record = [r for r in
            MARCReader(open(PROJECT_DIR + "/../test-helpers/files/books.mrc"),
            to_unicode=True)][0]

        self.leaderPositionEquals = Check(leader=5, operator=u"eq", values=u"c")
        self.leaderPositionEquals.save()
        self.fieldNotEqual = Check(field=u"245",operator=u"nq", values=u"Some unlikely book title")
        self.subfieldEquals = Check(field=u"245", subfield=u"a", operator=u"eq", values=u"The alpha masters :")
        self.indicatorIn = Check(field=u"245", indicator=u"1", operator=u"cn", values=u"0,4")
        self.subfieldExists = Check(field=u"245", subfield=u"a", operator=u"ex")
        self.subfieldDoesntExist = Check(field=u"245", subfield=u"q", operator=u"nx")
        self.nonExistentFieldSubfield = Check(field=u"301", subfield=u"a", operator=u"eq", values=u"")
        self.regexpOperator = Check(field=u"300", subfield=u"a", operator=u"re", values=u"\d+")

        self.report = Report(title="Testing Report 1", creator=user)
        self.report.save()
        self.report.checks.add(self.leaderPositionEquals)
        self.report.save()


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
            u"Returns that " + str(bool(self.record[self.subfieldDoesntExist.field][self.subfieldDoesntExist.subfield])) +  u" implies existence")
        self.assertTrue(self.leaderPositionEquals.run(self.record),
            u"Returns False on " + self.record.leader[self.leaderPositionEquals.leader] +
            u" == " + self.leaderPositionEquals.values)
        self.assertEquals(self.nonExistentFieldSubfield.run(self.record),
            u"Field 301 does not exist",
            u"Should return error message if" + self.nonExistentFieldSubfield.field+ u" does not exist" )
        self.assertTrue(self.regexpOperator.run(self.record),
            u"Field 300 should contain a number" )

    def test_helper_methods(self):
        #Leader helper - determines if the check should evaluate the record leader
        self.assertTrue(self.leaderPositionEquals._leader(),
            u"Returns False that leader exists when it is not present")
        self.assertFalse(self.fieldNotEqual._leader(),
            u"Returns True that leader exists when it is not present")
        #Field helper - determines if the check should evaluate the record field
        self.assertTrue(self.fieldNotEqual._field(),
            u"Returns False that field exists and/or subfield and/or indicator do not")
        self.assertFalse(self.subfieldEquals._field(),
            u"Returns True that field doesnt exist and/or subfield or indicator does ")
        #Subfield helper - determines if the check should evaluate the record subfield
        self.assertTrue(self.subfieldEquals._subfield(),
            u"Returns False that subfield exists when it is present")
        self.assertFalse(self.indicatorIn._subfield(),
            u"Returns True that subfield exists when it is not present")
        #indicator helper - determines if the check should evaluate the record indicator
        self.assertTrue(self.indicatorIn._indicator(),
            u"Returns False that indicator exists and subfield doesn't")
        self.assertFalse(self.subfieldEquals._indicator(),
            u"Returns True that indicator exists or subfield doesn't")
        #Should only return functions
        self.assertTrue(hasattr(self.leaderPositionEquals._select_operation_function(), "__call__" ),
            u"Should return a function that is callable")

    def test_views(self):

        user = self.c.login(username='tester',  password='tester')
        response = self.c.get('/report/list/' , follow=True)
        h = response.status_code
        self.assertEquals(response.status_code ,200,
            "It should be a 200 response status, but instead it is" + str(response.status_code)  )


    def tearDown(self):
        self.record = None
        self.fieldNotEqual = None
        self.subfieldEquals = None
        self.indicatorIn = None
        self.subfieldExists = None
