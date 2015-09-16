#!/usr/bin/env python
# (C) Copyright 2015 Hewlett Packard Enterprise Development LP.
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

import argparse
import os
import json
import sys

import ovs.dirs
from ovs.db import error
from ovs.db import types
import ovs.db.idl
from dhcp_lease_db import DHCPLeaseDB

vlog = ovs.vlog.Vlog("dhcp_leases")

def print_to_stdout(dhcp_lease_entry):
    print "%s %s %s %s %s" % \
           (dhcp_lease_entry["expiry_time"], \
            dhcp_lease_entry["mac_address"], \
            dhcp_lease_entry["ip_address"], \
            dhcp_lease_entry["client_hostname"], \
            dhcp_lease_entry["client_id"])

def dhcp_leases_show():

    dhcp_leases = DHCPLeaseDB()

    dhcp_lease_entry = {}

    # OPS_TODO:
    # Print dhcp_leases.idl.change_seqno
    for ovs_rec in dhcp_leases.idl.tables["DHCP_Lease"].rows.itervalues():
        dhcp_lease_entry = {"expiry_time":"*", "mac_address":"*",
                            "ip_address":"*", "client_hostname":"*",
                            "client_id":"*"}

        if ovs_rec.expiry_time and ovs_rec.expiry_time != None:
            dhcp_lease_entry["expiry_time"] = ovs_rec.expiry_time
        if ovs_rec.mac_address and ovs_rec.mac_address != None:
            dhcp_lease_entry["mac_address"] = ovs_rec.mac_address
        if ovs_rec.ip_address and ovs_rec.ip_address != None:
            dhcp_lease_entry["ip_address"] = ovs_rec.ip_address
        if ovs_rec.client_hostname and ovs_rec.client_hostname != None:
            dhcp_lease_entry["client_hostname"] = ovs_rec.client_hostname[0]
        if ovs_rec.client_id and ovs_rec.client_id != None:
            dhcp_lease_entry["client_id"] = ovs_rec.client_id[0]

        print_to_stdout(dhcp_lease_entry)

    dhcp_leases.close()

def dhcp_leases_add(dhcp_lease_entry):

    dhcp_leases = DHCPLeaseDB()

    row, status = dhcp_leases.insert_row(dhcp_lease_entry)

    if status != ovs.db.idl.Transaction.SUCCESS:
        vlog.err("dhcp_leases insert_row failed")

    dhcp_leases.close()

def dhcp_leases_update(dhcp_lease_entry):

    dhcp_leases = DHCPLeaseDB()

    row, status = dhcp_leases.update_row(dhcp_lease_entry["mac_address"],
                                         dhcp_lease_entry)

    if status != ovs.db.idl.Transaction.SUCCESS:
        vlog.err("dhcp_leases update_row failed")

    dhcp_leases.close()

def dhcp_leases_delete(dhcp_lease_entry):

    dhcp_leases = DHCPLeaseDB()

    row, status = dhcp_leases.delete_row(dhcp_lease_entry["mac_address"])

    if status != ovs.db.idl.Transaction.SUCCESS:
        vlog.err("dhcp_leases delete_row failed")

    dhcp_leases.close()


def main():

    dhcp_lease_entry = {"expiry_time":"*", "mac_address":"*", "ip_address":"*",
                        "client_hostname":"*", "client_id":"*"}

    argv = sys.argv
    num_args = len(argv)

    if num_args < 2:
        vlog.err("Error in arguments passed to dhcp_leases script, Exiting")
        sys.exit()

    parser = argparse.ArgumentParser()

    '''
    Dnsmasq invokes this script as:
      - dhcp_leases init
      - dhcp_leases add <mac_addr> <ip_addr> <hostname> <client-id>
      - dhcp_leases del <mac_addr> <ip_addr> <hostname> <client-id>
      - dhcp_leases old <mac_addr> <ip_addr> <hostname> <client-id>
    If the DHCP clients don't send hostname or client-id, dnsmasq wouldn't
    pass the values for it while invoking dhcp_leases script. So, the number
    of arguments would vary for any command.

    OPS_TODO:
      Fix the folllowing argument parsing - instead of parsing it based on
      the number of arguments, do it in a generic way that handles all the
      cases.
    '''
    parser.add_argument(action="store", dest='command')
    if num_args > 2:
        parser.add_argument(action="store", dest='mac_address')
    if num_args > 3:
        parser.add_argument(action="store", dest='ip_address')
    if num_args > 4:
        parser.add_argument(action="store", dest='client_hostname')
    if num_args > 5:
        parser.add_argument(action="store", dest='client_id')

    args = parser.parse_args()

    if num_args > 2:
        dhcp_lease_entry["mac_address"] = args.mac_address
        dhcp_lease_entry["expiry_time"] = os.environ["DNSMASQ_LEASE_EXPIRES"]
    if num_args > 3:
        dhcp_lease_entry["ip_address"] = args.ip_address
    if num_args > 4:
        dhcp_lease_entry["client_hostname"] = args.client_hostname
    if num_args > 5:
        dhcp_lease_entry["client_id"] = args.client_id

    command = args.command

    if command == "init" or command == "show":
        dhcp_leases_show()
    elif command == "add":
        dhcp_leases_add(dhcp_lease_entry)
    elif command == "del":
        dhcp_leases_delete(dhcp_lease_entry)
    elif command == "old":
        dhcp_leases_update(dhcp_lease_entry)
    elif command == "tftp":
        sys.exit()
    else:
        vlog.err("Invalid command %s to dhcp_leases script.... Exiting" \
              % (command))
        sys.exit()


if __name__ == '__main__':
    try :
        main()
        sys.exit()
    except error.Error, e:
        vlog.err("Error: \"%s\" \n" % e)
