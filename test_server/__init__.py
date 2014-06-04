# -*- coding: utf-8 -*-

import os
import sys
import time
from subprocess import Popen, check_call

import ldapom

if sys.version_info[0] >= 3: # Python 3
    unicode = str

MODULE_PATH = os.path.realpath(os.path.dirname(__file__))
MODULE_PATH_AS_URL = unicode(MODULE_PATH).replace("/", "%2F")
DEFAULT_CONFIG_FILE_PATH = os.path.join(MODULE_PATH, "slapd.conf")


class LDAPServer(object):
    """Represents and manages an OpenLDAP server."""

    def __init__(self, port=1381, tls_port=1382, config_file_path=None,
            working_dir_path=None):
        self.port = port
        self.tls_port = tls_port
        self.config_file_path = config_file_path or DEFAULT_CONFIG_FILE_PATH
        self.working_dir_path = working_dir_path or MODULE_PATH

    ## Load sample data into the LDAP server.
    def load_data(self, ldif_filename="testdata.ldif"):
        """Load sample data from an LDIF file in the working directory."""
        check_call(['rm', '-rf',
            '{}/ldapdata'.format(self.working_dir_path)])
        check_call(['mkdir', '-p',
            '{}/ldapdata'.format(self.working_dir_path)])
        dev_null = open("/dev/null", "w")
        check_call(['slapadd',
            '-l', os.path.join(self.working_dir_path, ldif_filename),
            '-f', self.config_file_path, '-d', '0'],
            stdout=dev_null, cwd=self.working_dir_path)
        dev_null.close()

    def ldapi_url(self):
        """The ldapi://-URL of this LDAP server."""
        return "ldapi://{0}%2Fldapi".format(MODULE_PATH_AS_URL)

    def start(self, clean=True):
        """Start the LDAP server."""
        if clean:
            self.load_data()
        self.server_process = Popen(['slapd', 
            '-f', self.config_file_path,
            '-h', self.ldapi_url(),
            '-d', '0'], cwd=self.working_dir_path)
        # Busy wait until LDAP is ready
        tries = 0
        while tries < 100:
            tries += 1
            try:
                ldapom.LDAPConnection(self.ldapi_url(),
                        base="dc=example,dc=com",
                        bind_dn="cn=admin,dc=example,dc=com",
                        bind_password="admin")
                return
            except ldapom.LDAPServerDownError:
                time.sleep(0.2)

    def stop(self):
        """ Stop the LDAP server."""
        if self.server_process is not None:
            self.server_process.terminate()
        self.server = None

    def restart(self):
        """Restart the LDAP server without clearing all data."""
        self.stop()
        self.start(clean=False)

