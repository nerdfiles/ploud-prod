#-----------------------------------------------------------------------------#
#   tests.py                                                                  #
#                                                                             #
#           Copyright (c) 2010-2011, Enfold Systems, Inc.                     #
#           All rights reserved.                                              #
#                                                                             #
#               This software is licensed under the Terms and Conditions      #
#               contained within the "LICENSE.txt" file that accompanied      #
#               this software.  Any inquiries concerning the scope or         #
#               enforceability of the license should be addressed to:         #
#                                                                             #
#                   Enfold Systems, Inc.                                      #
#                   4617 Montrose Blvd., Suite C215                           #
#                   Houston, Texas 77006 USA                                  #
#                   p. +1 713.942.2377 | f. +1 832.201.8856                   #
#                   www.enfoldsystems.com                                     #
#                   info@enfoldsystems.com                                    #
#-----------------------------------------------------------------------------#
""" tests """
import unittest, doctest, sys, smtplib, tempfile

from pyramid.config import Configurator

import ploud
from ploud.utils import ploud_config
from ploud.frontend.models import initialize_sql

from memphis import config
from memphis.config import testing


emails = []
configFile = None

class SMTP(object):

    def __init__(self, *args):
        pass

    def quit(self):
        pass

    def sendmain(self, fromaddr, toaddr, message):
        if getattr(self, 'raiseError', False):
            raise ValueError

        emails.append((fromaddr, toaddr, message))


def getEMails(clear=True):
    global emails
    m = list(emails)
    if clear:
        emails = []
    return m


def setUp(test):
    config.loadPackage('ploud.frontend')

    testing.setUpConfig(test)
    testing.setUpTestAsModule(test, 'ploud.TESTS')
    ploud.TESTS = sys.modules['ploud.TESTS']

    initialize_sql('sqlite://')

    smtplib.SMTP = SMTP

    global configFile
    hnd, configFile = tempfile.mkstemp()
    f = open(configFile, 'wb')
    f.write("""[frontend]\nregistration=true""")
    f.close()
    ploud_config.initializeConfig(configFile, True)

    pyramid_config = Configurator()
    pyramid_config.begin()


def tearDown(test):
    testing.tearDownTestAsModule(test)
    testing.tearDownConfig(test)
    del ploud.TESTS


def test_suite():
    return unittest.TestSuite((
            doctest.DocFileSuite(
                'tests.txt',
                setUp=setUp, tearDown=tearDown,
                optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        ))
