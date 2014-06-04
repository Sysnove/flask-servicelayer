#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from ldapom import LDAPConnection
from ldapom_model import LDAPModel, LDAPAttr
from flask.ext.servicelayer import LDAPOMService
import test_server

import werkzeug

class LDAPServerMixin(object):

    """Mixin to set up an LDAPConnection connected to a testing LDAP server."""

    def setUp(self):
        self.ldap_server = test_server.LDAPServer()
        self.ldap_server.start()
        self.ldap = LDAPConnection(
                uri=self.ldap_server.ldapi_url(),
                base='dc=example,dc=com',
                bind_dn='cn=admin,dc=example,dc=com',
                bind_password='admin')

    def tearDown(self):
        self.ldap_server.stop()


class Person(LDAPModel):
    _class = 'person'
    _class_attrs = {'cn': LDAPAttr('cn'),
                    'lastname': LDAPAttr('sn', server_default="Default"),
                    'invalidAttribute': LDAPAttr('invalid'),
                    'shell': LDAPAttr('loginShell'),
                    'phone': LDAPAttr('telephoneNumber', multiple=True),
                    'home': LDAPAttr('homeDirectory', nullable=False),
                    'description': LDAPAttr('description', default="Default"),
                    'photo': LDAPAttr('jpegPhoto')}
    _rdn = 'cn'

    def __str__(self):
        return self.name

    @property
    def name(self):
        return ' '.join([self.givenName, self.sn]) if self.givenName else self.sn


class PersonService(LDAPOMService):
    __model__ = Person

    def __init__(self, ldap):
        super().__init__()
        self.__ldap__ = ldap
    

class TestLDAPModel(LDAPServerMixin, unittest.TestCase):

    def setUp(self):
        super().setUp() 
        self.service = PersonService(self.ldap)

    def test_ok(self):
        self.assertTrue(True)

    def test_all(self):
        people = self.service.all()
        self.assertEqual(len(people), 4)

    def test_get(self):
        self.service.get("jack")
        with self.assertRaises(Exception):
            self.service.get("nobody")
        with self.assertRaises(Exception):
            self.service.get("*a*")

    def test_get_or_404(self):
        self.service.get_or_404("jack")
        with self.assertRaises(werkzeug.exceptions.NotFound):
            self.service.get_or_404("nobody")
        with self.assertRaises(Exception):
            self.service.get_or_404("*a*")

    def test_get_all(self):
        people = self.service.get_all("sam")
        self.assertEqual(len(people), 1)
        people = self.service.get_all("sam", "jack")
        self.assertEqual(len(people), 2)
        with self.assertRaises(Exception):
            people = self.service.get_all("nobody")

    def test_find(self):
        people = self.service.find()
        self.assertEqual(len(people), 4)
        people = self.service.find(shell="/bin/bash")
        self.assertEqual(len(people), 4)
        people = self.service.find(lastname="Carter")
        self.assertEqual(len(people), 1)
        self.assertEqual(people[0].cn, "sam")
        people = self.service.find(lastname="Carter", shell="/bin/bash")
        self.assertEqual(len(people), 1)
        people = self.service.find(lastname="nobody")
        self.assertEqual(len(people), 0)
        # :TODO:maethor:140604: search with multiple values attribute ?

    def test_first(self):
        self.service.first()
        self.service.first(shell="/bin/bash")
        self.service.first(lastname="Carter")
        with self.assertRaises(Exception):
            self.service.first(lastname="nobody")

    def test_one(self):
        self.service.one(lastname="Carter")
        with self.assertRaises(Exception):
            self.service.one(shell="/bin/bash")
        with self.assertRaises(Exception):
            self.service.first(lastname="nobody")

    def test_new(self):
        george = self.service.new(cn="george", lastname="Hammond")
        self.assertEqual(george.cn, "george")
        self.assertEqual(george.lastname, "Hammond")
        self.assertEqual(george.dn, "cn=george,dc=example,dc=com")
        with self.assertRaises(Exception):
            self.service.get("george")
        george = self.service.save(george)
        self.assertEqual(george.cn, "george")
        george = self.service.get("george")
        self.assertEqual(george.dn, "cn=george,dc=example,dc=com")

    def test_create(self):
        george = self.service.create(cn="george", lastname="Hammond")
        self.assertEqual(george.cn, "george")
        self.service.get("george")
        with self.assertRaises(Exception):
            george = self.service.create(cn="sam", lastname="Hammond")

    def test_update(self):
        jack = self.service.get("jack")
        self.assertEqual(jack.shell, "/bin/bash")
        self.service.update(jack, shell="/bin/zsh")
        self.assertEqual(jack.shell, "/bin/zsh")
        jack = self.service.get("jack")
        self.assertEqual(jack.shell, "/bin/zsh")
        self.service.update(jack, shell="/bin/bash", phone="4242424242")
        jack = self.service.get("jack")
        self.assertEqual(jack.shell, "/bin/bash")
        self.assertEqual(jack.phone, {"4242424242"})

    def test_delete(self):
        jack = self.service.get("jack")
        self.service.delete(jack)
        with self.assertRaises(Exception):
            self.service.get("jack")

    def test_paginate(self):
        # :TODO:maethor:140604: 
        pass

if __name__ == '__main__':
    unittest.main()
