from django.utils import unittest
from check.models import *

class CheckTest(unittest.TestCase):
    def setUp(self):
        self.fieldNotEqual = Check(field=u"245", operator=u"nq",values=u"Some unlikely book title")

    def test_unicode_display(self):
        self.assertEqual(self.fieldNotEqual.__unicode__(),
            u"Field 245 is not equal to Some unlikely book title",
            "Unicode representation does not match expected result")

    def tearDown(self):
        self.fieldNotEqual.dispose()
        self.fieldNotEqual = None
