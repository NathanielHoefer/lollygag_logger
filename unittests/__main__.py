import unittest

import test_vlogfield
import test_vlogline
import test_vutils

suite_loader = unittest.TestLoader()
modules = [
    suite_loader.loadTestsFromModule(test_vlogfield),
    suite_loader.loadTestsFromModule(test_vlogline),
    suite_loader.loadTestsFromModule(test_vutils)
]
suite = unittest.TestSuite(modules)

unittest.TextTestRunner().run(suite)
