# Copyright (C) 2014-2015 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License..

import os
import sys
from time import sleep

import ovs.dirs
from ovs.db import error
from ovs.db import types
import ovs.db.idl
import ovs.vlog

vlog = ovs.vlog.Vlog("dhcp_lease_db")

# ovs definitions
idl = None
# HALON_TODO: Need to pull this from the build env
def_db = 'unix:/var/run/openvswitch/db.sock'

# HALON_TODO: Need to pull this from the build env
dhcp_lease_db_schema = '/usr/share/openvswitch/dhcp_leases.ovsschema'

max_time_to_wait_for_dhcp_lease_data = 30

#DHCP lease tabe names
DHCP_LEASES_TABLE = "DHCP_Lease"

#DHCP lease db column names
TIME = "expiry_time"
MAC_ADDR = "mac_address"
IP_ADDR = "ip_address"
CLIENT_HOSTNAME = "client_hostname"
CLIENT_ID = "client_id"

class Dhcp_lease_db(object):
    def __init__(self, location=None):
        '''
        Creates a Idl connection to the DHCP lease db and register all the
        columns with schema helper.

        Maintain the self global value for all the columns in configdb that
        can be modified and updated to existing row or inserted as new row.
        '''
        self.idl = None
        self.txn = None
        self.schema_helper = ovs.db.idl.SchemaHelper(location=dhcp_lease_db_schema)
        self.schema_helper.register_table(DHCP_LEASES_TABLE)

        self.idl = ovs.db.idl.Idl(def_db, self.schema_helper)

        self.expiry_time = None
        self.mac_address = None
        self.ip_address = None
        self.client_hostname = None
        self.client_id = None

        '''
        The wait time is 30 * 0.1 = 3 seconds
        '''
        cnt = max_time_to_wait_for_dhcp_lease_data
        while not self.idl.run() and cnt > 0:
            cnt -= 1
            sleep(.1)

    def find_row_by_mac_addr(self, mac_addr):
        '''
        Walk through the rows in the dhcp lease table (if any)
        looking for a row with mac addr passed in argument

        If row found set variable tbl_found to True and return
        the row object to caller function
        '''
        tbl_found = False
        ovs_rec = None
        for ovs_rec in self.idl.tables[DHCP_LEASES_TABLE].rows.itervalues():
            if ovs_rec.mac_address == mac_addr:
                tbl_found = True
                break

        return ovs_rec, tbl_found

    def __set_column_value(self, row, entry):
        status = "success"

        if entry["expiry_time"] != None:
            setattr(row, TIME, entry["expiry_time"])

        if entry["mac_addr"] != None:
            setattr(row, MAC_ADDR, entry["mac_addr"])

        if entry["ip_addr"] != None:
            setattr(row, IP_ADDR, entry["ip_addr"])

        if entry["client_hostname"] != None:
            setattr(row, CLIENT_HOSTNAME, entry["client_hostname"])

        if entry["client_id"] != None:
            setattr(row, CLIENT_ID, entry["client_id"])

        return status

    def insert_row(self, entry):
        '''
        Insert a new row in dhcp_lease_db and update the columns with
        user values (default values are taken if columns values
        not given by user) in global variables.
        '''
        self.txn = ovs.db.idl.Transaction(self.idl)
        row = self.txn.insert(self.idl.tables[DHCP_LEASES_TABLE])

        status = self.__set_column_value(row, entry)

        if (status != "success"):
            return None, status
        else :
            status = self.txn.commit_block()

        return row, status

    def update_row(self, mac_addr, entry):
        '''
        Update the row with the latest modified values.
        '''
        self.txn = ovs.db.idl.Transaction(self.idl)
        row, row_found = self.find_row_by_mac_addr(mac_addr)

        if row_found:
            status = self.__set_column_value(row, entry)

            if (status != "success"):
                return None, status
            else :
                status = self.txn.commit_block()

        else:
            row, status = self.insert_row(entry)

        return row, status

    def delete_row(self, mac_addr):
        '''
        Delete a specific row from dhcp_lease_db based on
        mac addr passed as argument

        If specified row is found, variable row_found
        is updated to True and delete status is returned
        '''
        self.txn = ovs.db.idl.Transaction(self.idl)
        row, row_found = self.find_row_by_mac_addr(mac_addr)
        status = "unchanged"

        if row_found:
            row.delete()
            status = self.txn.commit_block()

        return row_found, status

    def close(self):
         self.idl.close()
