#!/usr/bin/env python
# (C) Copyright 2015 Hewlett Packard Enterprise Development LP
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

'''
NOTES:
 - DHCP-TFTP python daemon. This is a helper daemon
   to retrieve the DHCP-TFTP server configs from OVSDB
   during bootup and starts the dnsmasq dameon (open source
   daemon for DHCP-TFTP functionality). Then it monitors
   OVSDB for any config changes related to DHCP-TFTP server
   and if there is any it kills dnsmasq daemon and restarts
   with new config.
'''

import argparse
import os
import sys
import subprocess
from time import sleep
import signal

import ovs.dirs
from ovs.db import error
from ovs.db import types
import ovs.daemon
import ovs.db.idl
import ovs.unixctl
import ovs.unixctl.server

# OVS definitions
idl = None

# Tables definitions
SYSTEM_TABLE = 'System'
VRF_TABLE = 'VRF'
DHCP_SERVER_TABLE = 'DHCP_Server'
DHCP_SERVER_RANGE_TABLE = 'DHCPSrv_Range'
DHCP_SERVER_STATIC_HOST_TABLE = 'DHCPSrv_Static_Host'
DHCP_SERVER_OPTION_TABLE = 'DHCPSrv_Option'
DHCP_SERVER_MATCH_TABLE = 'DHCPSrv_Match'

# Columns definitions - System Table
SYSTEM_VRFS = 'vrfs'
SYSTEM_CUR_CFG = 'cur_cfg'
SYSTEM_OTHER_CONFIG = 'other_config'

# Columns definitions - VRF Table
VRF_NAME = 'name'
VRF_DHCP_SERVER = 'dhcp_server'
VRF_OTHER_CONFIG = 'other_config'

# Columns definitions - DHCPSrv_Range Table
DHCP_RANGE_START_IP = 'start_ip_address'
DHCP_RANGE_END_IP = 'end_ip_address'
DHCP_RANGE_TAG = 'tag'
DHCP_RANGE_MODE = 'mode'
DHCP_RANGE_LEASE_DURATION = 'lease_duration'

# Columns definitions - DHCPSrv_Host Table
DHCP_HOST_MAC_ADDRESS = 'mac_address'
DHCP_HOST_TAG = 'tag'
DHCP_HOST_IP_ADDRESS = 'ip_address'
DHCP_HOST_CLIENT_NAME = 'client_hostname'
DHCP_HOST_CLIENT_ID = 'client_id'

# Columns definitions - DHCPSrv_Option Table
DHCP_OPTION_TAG = 'tag'
DHCP_OPTION_NAME = 'option_name'
DHCP_OPTION_NUMBER = 'option_number'
DHCP_OPTION_VALUE = 'option_value'
DHCP_OPTION_IPV6 = 'ipv6'

# Columns definitions - DHCPSrv_Boot Table
DHCP_BOOT_TAG = 'tag'
DHCP_BOOT_FILE_NAME = 'file_name'

# Default DB path
def_db = 'unix:/var/run/openvswitch/db.sock'

# OPS_TODO: Need to pull these from the build env
ovs_schema = '/usr/share/openvswitch/vswitch.ovsschema'

vlog = ovs.vlog.Vlog("dhcp_tftp")
exiting = False
seqno = 0

dnsmasq_process = None
dnsmasq_started = False
dnsmasq_command = None
dhcp_range_config = False

# OPS_TODO: Remove the log facility option before final release
dnsmasq_default_command = ('/usr/bin/dnsmasq --port=0 --user=root '
                           '--dhcp-script=/usr/bin/dhcp_leases --leasefile-ro '
                           '--log-facility=/tmp/dnsmasq.log ')
dnsmasq_dhcp_range_option = '--dhcp-range='
dnsmasq_dhcp_host_option = '--dhcp-host='
dnsmasq_dhcp_option_arg = '--dhcp-option='
dnsmasq_dhcp_boot_option = '--dhcp-boot='


def unixctl_exit(conn, unused_argv, unused_aux):
    global exiting
    exiting = True
    conn.reply(None)


# ------------------ db_get_system_status() ----------------
def db_get_system_status(data):
    '''
    Checks if the system initialization is completed.
    If System:cur_cfg > 0:
        configuration completed: return True
    else:
        return False
    '''
    for ovs_rec in data[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.cur_cfg:
            if ovs_rec.cur_cfg == 0:
                return False
            else:
                return True

    return False


# ------------------ system_is_configured() ----------------
def system_is_configured():
    global idl

    # Check the OVS-DB/File status to see if initialization has completed.
    if not db_get_system_status(idl.tables):
        return False

    return True


# ------------------ terminate() ----------------
def terminate():
    global exiting
    # Exiting daemon
    exiting = True


# ------------------ dhcp_tftp_init() ----------------
def dhcp_tftp_init(remote):
    '''
    Initializes the OVS-DB connection
    '''

    global idl

    schema_helper = ovs.db.idl.SchemaHelper(location=ovs_schema)
    schema_helper.register_columns(SYSTEM_TABLE,
                                   [SYSTEM_VRFS, SYSTEM_CUR_CFG,
                                    SYSTEM_OTHER_CONFIG])
    schema_helper.register_columns(VRF_TABLE,
                                   [VRF_NAME, VRF_DHCP_SERVER,
                                    VRF_OTHER_CONFIG])
    schema_helper.register_table(DHCP_SERVER_TABLE)
    schema_helper.register_table(DHCP_SERVER_RANGE_TABLE)
    schema_helper.register_table(DHCP_SERVER_STATIC_HOST_TABLE)
    schema_helper.register_table(DHCP_SERVER_OPTION_TABLE)
    schema_helper.register_table(DHCP_SERVER_MATCH_TABLE)

    idl = ovs.db.idl.Idl(remote, schema_helper)


# ------------------ dhcp_tftp_get_config() ---------
def dhcp_tftp_get_config():

    global idl
    global dnsmasq_command
    global dnsmasq_default_command
    global dhcp_range_config
    global dnsmasq_started

    vrf_row = None
    dhcp_server_rec = None
    dhcpsrv_range_table = None
    ovs_rec = None
    dhcp_leases_command = None

    range_options = None
    static_host_options = None

    tags = []
    dhcp_range = []
    dhcp_host = []
    dhcp_option = []
    dhcp_boot = []

    dnsmasq_command = dnsmasq_default_command
    vlog.dbg("dhcp_tftp_debug - dnsmasq_command(1) %s "
             % (dnsmasq_command))

    # Get the dhcp server ranges config first
    for ovs_rec in idl.tables[DHCP_SERVER_RANGE_TABLE].rows.itervalues():
        dhcp_range_config = True
        range_options = ""
        if ovs_rec.match_tags and ovs_rec.match_tags is not None:
            tags = ovs_rec.match_tags
            for each_tag in tags:
                range_options = range_options + 'tag:' + each_tag + ','

        if ovs_rec.set_tag and ovs_rec.set_tag is not None:
            tags = ovs_rec.set_tag
            for each_tag in tags:
                range_options = range_options + 'set:' + each_tag + ','

        if ovs_rec.start_ip_address and ovs_rec.start_ip_address is not None:
            range_options = range_options + ovs_rec.start_ip_address

        if ovs_rec.end_ip_address and ovs_rec.end_ip_address is not None:
            range_options = range_options + ',' + ovs_rec.end_ip_address[0]

        if ovs_rec.is_static and ovs_rec.is_static is not None:
            if ovs_rec.is_static[0] == True:
                range_options = range_options + ',' + 'static'

        if ovs_rec.netmask and ovs_rec.netmask is not None:
            range_options = range_options + ',' + ovs_rec.netmask[0]

        if ovs_rec.broadcast and ovs_rec.broadcast is not None:
            range_options = range_options + ',' + ovs_rec.broadcast[0]

        if ovs_rec.prefix_len and ovs_rec.prefix_len is not None:
            if ovs_rec.prefix_len[0] != 64:
                range_options = range_options + ',' + \
                                str(ovs_rec.prefix_len[0])

        if ovs_rec.lease_duration and ovs_rec.lease_duration is not None:
            if ovs_rec.lease_duration[0] == 0:
                range_options = range_options + ',' + 'infinite'
            else:
                range_options = range_options + ',' + \
                                str(ovs_rec.lease_duration[0]) + 'm'

        vlog.dbg("dhcp_tftp_debug - dhcp_range %s "
                 % (range_options))
        dnsmasq_command = dnsmasq_command + ' --dhcp-range=' + range_options
        vlog.dbg("dhcp_tftp_debug - dnsmasq cmd %s "
                 % (dnsmasq_command))
        # print dnsmasq_command

    if dhcp_range_config == False and dnsmasq_started == False:
        dhcp_leases_command = "/usr/bin/dhcp_leases clear"
        dnsmasq_process = subprocess.Popen(dhcp_leases_command,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, shell=True)

        err = dnsmasq_process.stderr.read()
        print err
        if err != "":
           vlog.emer("%s" % (err))
           vlog.emer("Error with config, dnsmasq failed, command %s" %
                  (dhcp_leases_command))

    # Get the dhcp server static hosts config
    for ovs_rec in idl.tables[DHCP_SERVER_STATIC_HOST_TABLE].rows.itervalues():
        static_host_options = ""
        if ovs_rec.mac_addresses and ovs_rec.mac_addresses is not None:
            macs = ovs_rec.mac_addresses
            for each_mac in macs:
                static_host_options = static_host_options + each_mac + ','

        if ovs_rec.client_id and ovs_rec.client_id is not None:
            static_host_options = static_host_options + 'id:' + \
                                  ovs_rec.client_id[0] + ','

        if ovs_rec.set_tags and ovs_rec.set_tags is not None:
            tags = ovs_rec.set_tags
            for each_tag in tags:
                static_host_options = static_host_options + 'set:' + \
                                      each_tag + ','

        if ovs_rec.ip_address and ovs_rec.ip_address is not None:
            static_host_options = static_host_options + ovs_rec.ip_address

        if ovs_rec.client_hostname and ovs_rec.client_hostname is not None:
            static_host_options = static_host_options + ',' + \
                                  ovs_rec.client_hostname[0]

        if ovs_rec.lease_duration and ovs_rec.lease_duration is not None:
            if ovs_rec.lease_duration[0] == 0:
                static_host_options = static_host_options + ',' + 'infinite'
            else:
                static_host_options = static_host_options + ',' + \
                                      str(ovs_rec.lease_duration[0]) + 'm'

        vlog.dbg("dhcp_tftp_debug - dhcp_host %s "
                 % (static_host_options))
        dnsmasq_command = dnsmasq_command + ' --dhcp-host=' + \
            static_host_options
        vlog.dbg("dhcp_tftp_debug - dnsmasq cmd %s "
                 % (dnsmasq_command))
        # print dnsmasq_command

    # Get the dhcp server options config
    for ovs_rec in idl.tables[DHCP_SERVER_OPTION_TABLE].rows.itervalues():
        dhcp_options = ""
        if ovs_rec.match_tags and ovs_rec.match_tags is not None:
            tags = ovs_rec.match_tags
            for each_tag in tags:
                dhcp_options = dhcp_options + 'set:' + each_tag + ','

        if ovs_rec.option_name and ovs_rec.option_name is not None:
            if ovs_rec.ipv6 and ovs_rec.ipv6 is not None:
                if ovs_rec.ipv6[0] == True:
                    dhcp_options = dhcp_options + 'option6:'
                else:
                    dhcp_options = dhcp_options + 'option:'
            else:
                dhcp_options = dhcp_options + 'option:'

            dhcp_options = dhcp_options + ovs_rec.option_name[0]
        else:
            dhcp_options = dhcp_options + str(ovs_rec.option_number[0])

        if ovs_rec.option_value and ovs_rec.option_value is not None:
            dhcp_options = dhcp_options + ',' + ovs_rec.option_value[0]

        vlog.dbg("dhcp_tftp_debug - dhcp_option %s "
                 % (dhcp_options))
        dnsmasq_command = dnsmasq_command + ' --dhcp-option=' + dhcp_options
        vlog.dbg("dhcp_tftp_debug - dnsmasq cmd %s "
                 % (dnsmasq_command))
        # print dnsmasq_command

    # Get the dhcp server matches config
    for ovs_rec in idl.tables[DHCP_SERVER_MATCH_TABLE].rows.itervalues():
        match_options = ""
        if ovs_rec.set_tag and ovs_rec.set_tag is not None:
            match_options = match_options + 'set:' + ovs_rec.set_tag + ','

        if ovs_rec.option_name and ovs_rec.option_name is not None:
            match_options = match_options + 'option:' + ovs_rec.option_name[0]
        else:
            match_options = match_options + str(ovs_rec.option_number[0])

        if ovs_rec.option_value and ovs_rec.option_value is not None:
            match_options = match_options + ',' + ovs_rec.option_value[0]

        vlog.dbg("dhcp_tftp_debug - dhcp match %s "
                 % (match_options))
        dnsmasq_command = dnsmasq_command + ' --dhcp-match=' + match_options
        vlog.dbg("dhcp_tftp_debug - dnsmasq cmd %s "
                 % (dnsmasq_command))
        # print dnsmasq_command

    # Get the dhcp server bootp config
    for ovs_rec in idl.tables[DHCP_SERVER_TABLE].rows.itervalues():
        if ovs_rec.bootp and ovs_rec.bootp is not None:
            bootp_options = ""
            bootp = {}
            bootp = ovs_rec.bootp
            for key, value in bootp.iteritems():
                bootp_options = ""
                if key == 'no_matching_tag':
                    bootp_options = value
                else:
                    bootp_options = 'tag:' + key + ',' + value

                vlog.dbg("dhcp_tftp_debug - dhcp boot %s "
                         % (bootp_options))
                dnsmasq_command = dnsmasq_command + ' --dhcp-boot=' + \
                    bootp_options
                vlog.dbg("dhcp_tftp_debug - dnsmasq cmd %s "
                         % (dnsmasq_command))
        # print dnsmasq_command

    # Get the tftp server config
    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.other_config and ovs_rec.other_config is not None:
            for key, value in ovs_rec.other_config.iteritems():
                if key == 'tftp_server_enable':
                    if value and value == 'true':
                        dnsmasq_command = dnsmasq_command + ' --enable-tftp '
                if key == 'tftp_server_secure':
                    if value and value == 'true':
                        dnsmasq_command = dnsmasq_command + ' --tftp-secure '
                if key == 'tftp_server_path':
                    if value and value is not None:
                        dnsmasq_command = dnsmasq_command + ' --tftp-root=' + \
                                          value

                vlog.dbg("dhcp_tftp_debug - dnsmasq cmd %s "
                         % (dnsmasq_command))
                # print dnsmasq_command

    vlog.info("dhcp_tftp_debug - dnsmasq_command(2) %s "
              % (dnsmasq_command))


# ------------------ dnsmasq_start_process() ----------
def dnsmasq_start_process():

    global dnsmasq_process
    global dnsmasq_command

    dnsmasq_process = None

    vlog.info("dhcp_tftp_debug - dnsmasq_command(3) %s "
              % (dnsmasq_command))

    dnsmasq_process = subprocess.Popen(dnsmasq_command,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)

    err = dnsmasq_process.stderr.read()
    print err
    if err != "":
        vlog.emer("%s" % (err))
        vlog.emer("Error with config, dnsmasq failed, command %s" %
                  (dnsmasq_command))
    else:
        vlog.info("dhcp_tftp_debug - dnsmasq started")


# ------------------ dnsmasq_run() ----------------
def dnsmasq_run():

    global idl
    global seqno
    global dnsmasq_started

    idl.run()

    if seqno != idl.change_seqno:
        vlog.info("dhcp_tftp_debug - seqno change from %d to %d "
                  % (seqno, idl.change_seqno))
        seqno = idl.change_seqno

        # Check if system is configured and startup config is restored
        if system_is_configured() == False:
            return
        else:
            # Get the dhcp-tftp config
            dhcp_tftp_get_config()

            # Start the dnsmasq
            dnsmasq_start_process()
            dnsmasq_started = True


# --------------------- dnsmasq_restart() --------------
def dnsmasq_restart():

    global idl
    global dnsmasq_process

    if dnsmasq_process is not None:
        vlog.dbg("dhcp_tftp_debug - killing dnsmasq")
        dnsmasq_process.kill()

    # Also check if any other dnsmasq process is running and kill
    # This needs to be done as dnsmasq binary forks multiple processes
    vlog.info("dhcp_tftp_debug (2) - killing dnsmasq")
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()

    for line in out.splitlines():
        if 'dnsmasq' in line:
            pid = int(line.split(None, 1)[0])
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                vlog.info("dhcp_tftp_debug - unable to kill previous process")
                pass

    # Get the config
    dhcp_tftp_get_config()

    # Start the dnsmasq process
    dnsmasq_start_process()


# ------------------ main() ----------------
def main():

    global exiting
    global idl
    global seqno
    global dnsmasq_started

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', metavar="DATABASE",
                        help="A socket on which ovsdb-server is listening.",
                        dest='database')

    ovs.vlog.add_args(parser)
    ovs.daemon.add_args(parser)
    args = parser.parse_args()
    ovs.vlog.handle_args(args)
    ovs.daemon.handle_args(args)

    if args.database is None:
        remote = def_db
    else:
        remote = args.database

    dhcp_tftp_init(remote)

    ovs.daemon.daemonize()

    ovs.unixctl.command_register("exit", "", 0, 0, unixctl_exit, None)
    error, unixctl_server = ovs.unixctl.server.UnixctlServer.create(None)

    if error:
        ovs.util.ovs_fatal(error, "dhcp_tftp_helper: could not create "
                                  "unix-ctl server", vlog)

    while dnsmasq_started is False:
        dnsmasq_run()
        sleep(2)

    seqno = idl.change_seqno    # Sequence number when we last processed the db

    exiting = False
    while not exiting:

        unixctl_server.run()

        if exiting:
            break

        if seqno == idl.change_seqno:
            poller = ovs.poller.Poller()
            unixctl_server.wait(poller)
            idl.wait(poller)
            poller.block()

        idl.run()  # Better reload the tables

        vlog.dbg("dhcp_tftp_debug main - seqno change from %d to %d "
                 % (seqno, idl.change_seqno))
        if seqno != idl.change_seqno:
            '''
            OPS_TODO:
              If seqno is changed, it is assumed that DHCP/TFTP server config
              parameters have been changed by user and hence dnsmasq is
              is restarted with new config.

              This needs to be fixed - even if seqno gets changed, we need
              to check if the DHCP/TFTP server configuration is really changed
              or not and restart the dnsmasq daemon only if the config had
              been changed.
            '''
            dnsmasq_restart()
            seqno = idl.change_seqno

    # Daemon exit
    unixctl_server.close()
    idl.close()


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except:
        vlog.exception("traceback")
        sys.exit(ovs.daemon.RESTART_EXIT_CODE)
