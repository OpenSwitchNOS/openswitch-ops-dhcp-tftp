#!/usr/bin/env python
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
OPEN_VSWITCH_TABLE = 'Open_vSwitch'
DHCP_RANGE_TABLE = 'DHCP_Range'
DHCP_HOST_TABLE = 'DHCP_Host'
DHCP_OPTION_TABLE = 'DHCP_Option'
DHCP_TFTP_INTERFACE_TABLE = 'DHCP_TFTP_Interfaces'

# Columns definitions - Open_vSwitch Table
OPEN_VSWITCH_CUR_CFG = 'cur_cfg'
OPEN_VSWITCH_DHCP_RANGE = 'dhcp_range'
OPEN_VSWITCH_DHCP_HOST = 'dhcp_host'
OPEN_VSWITCH_DHCP_OPTION = 'dhcp_option'
OPEN_VSWITCH_DHCP_TFTP_INTERFACES = 'dhcp_tftp_interfaces'
OPEN_VSWITCH_DHCP_TFTP_CONFIG = 'dhcp_tftp_config'

# Columns definitions - DHCP_Range Table
DHCP_RANGE_COLUMN = 'dhcp_range'

# Columns definitions - DHCP_Host Table
DHCP_HOST_COLUMN = 'dhcp_host'

# Columns definitions - DHCP_Option Table
DHCP_OPTION_COLUMN = 'dhcp_option'

# Columns definitions - DHCP_TFTP_Interfaces Table
DHCP_TFTP_INTERFACES_COLUMN = 'dhcp_tftp_interfaces'

# Default DB path
def_db = 'unix:/var/run/openvswitch/db.sock'

# HALON_TODO: Need to pull these from the build env
ovs_schema = '/usr/share/openvswitch/vswitch.ovsschema'

vlog = ovs.vlog.Vlog("dhcp_tftp")
exiting = False
seqno = 0

dnsmasq_process = None
dnsmasq_started = False
dnsmasq_command = None
#TODO: Remove the log facility option before final release
dnsmasq_default_command = ('/usr/bin/dnsmasq --port=0 --user=root '
                           '--dhcp-script=/usr/bin/dhcp_leases --leasefile-ro '
                           '--log-facility=/tmp/dnsmasq.log ')
dnsmasq_dhcp_range_option = '--dhcp-range='
dnsmasq_dhcp_host_option = '--dhcp-host='

def unixctl_exit(conn, unused_argv, unused_aux):
    global exiting
    exiting = True
    conn.reply(None)

#------------------ db_get_system_status() ----------------
def db_get_system_status(data):
    '''
    Checks if the system initialization is completed.
    If Open_vSwitch:cur_cfg > 0:
        configuration completed: return True
    else:
        return False
    '''
    for ovs_rec in data[OPEN_VSWITCH_TABLE].rows.itervalues():
        if ovs_rec.cur_cfg:
            if ovs_rec.cur_cfg == 0:
                return False
            else:
                return True

    return False

#------------------ system_is_configured() ----------------
def system_is_configured():
    global idl

    # Check the OVS-DB/File status to see if initialization has completed.
    if not db_get_system_status(idl.tables):
        return False

    return True

#------------------ terminate() ----------------
def terminate():
    global exiting
    #Exiting Daemon
    exiting = True


#------------------ dnsmasq_init() ----------------
def dnsmasq_init(remote):
    '''
    Initializes the OVS-DB connection
    '''

    global idl

    schema_helper = ovs.db.idl.SchemaHelper(location=ovs_schema)
    schema_helper.register_columns(OPEN_VSWITCH_TABLE, \
            [OPEN_VSWITCH_CUR_CFG, OPEN_VSWITCH_DHCP_RANGE, \
             OPEN_VSWITCH_DHCP_HOST, OPEN_VSWITCH_DHCP_OPTION, \
             OPEN_VSWITCH_DHCP_TFTP_INTERFACES, \
             OPEN_VSWITCH_DHCP_TFTP_CONFIG])
    schema_helper.register_table(DHCP_RANGE_TABLE)
    schema_helper.register_table(DHCP_HOST_TABLE)
    schema_helper.register_table(DHCP_OPTION_TABLE)
    schema_helper.register_table(DHCP_TFTP_INTERFACE_TABLE)

    idl = ovs.db.idl.Idl(remote, schema_helper)


#------------------ dnsmasq_get_config() ---------
def dnsmasq_get_config():

    global idl
    global dnsmasq_command
    global dnsmasq_default_command

    dhcp_range = []
    dhcp_host = []

    dnsmasq_command = dnsmasq_default_command
    vlog.dbg("dnsmasq_debug - dnsmasq_command(1) %s " \
                     % (dnsmasq_command))

    for ovs_rec in idl.tables[DHCP_RANGE_TABLE].rows.itervalues():
        if ovs_rec.dhcp_range:
            dhcp_range = ovs_rec.dhcp_range
            vlog.dbg("dnsmasq_debug - dhcp_range %s " \
                     % (dhcp_range))
            dnsmasq_command = dnsmasq_command + ' --dhcp-range=' + dhcp_range

    for ovs_rec in idl.tables[DHCP_HOST_TABLE].rows.itervalues():
        if ovs_rec.dhcp_host:
            dhcp_host = ovs_rec.dhcp_host
            vlog.dbg("dnsmasq_debug - dhcp_host %s " \
                     % (dhcp_host))
            dnsmasq_command = dnsmasq_command + ' --dhcp-host=' + dhcp_host

    '''
    if dhcp_range is not None:
        for each_range in dhcp_range:
            dnsmasq_command = dnsmasq_command + ' --dhcp-range=' + each_range

    if dhcp_host is not None:
        for each_host in dhcp_host:
            dnsmasq_command = dnsmasq_command + ' --dhcp-host=' + each_host
    '''

    vlog.dbg("dnsmasq_debug - dnsmasq_command(2) %s " \
                     % (dnsmasq_command))


#------------------ dnsmasq_start_process() ----------
def dnsmasq_start_process():

    global dnsmasq_process
    global dnsmasq_command

    dnsmasq_process = None

    vlog.info("dnsmasq_debug - dnsmasq_command(3) %s " \
                     % (dnsmasq_command))

    dnsmasq_process = subprocess.Popen(dnsmasq_command,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)


#------------------ dnsmasq_run() ----------------
def dnsmasq_run():

    global idl
    global seqno
    global dnsmasq_started

    idl.run()

    if seqno != idl.change_seqno:
        vlog.info("dnsmasq_debug - seqno change from %d to %d " \
                     % (seqno, idl.change_seqno))
        seqno = idl.change_seqno

        # Check if system is configured and startup config is restored
        if system_is_configured() == False:
            return
        else:
            # Get the dnsmasq config
            dnsmasq_get_config()

            # Start the dnsmasq
            dnsmasq_start_process()
            dnsmasq_started = True
            vlog.info("dnsmasq_debug - dnsmasq started")

#--------------------- dnsmasq_restart() --------------
def dnsmasq_restart():

    global idl
    global dnsmasq_process

    if dnsmasq_process is not None:
        vlog.dbg("dnsmasq_debug - killing dnsmasq")
        dnsmasq_process.kill()

    # Also check if any other dnsmasq process is running and kill
    # This needs to be done as dnsmasq binary forks multiple processes
    vlog.info("dnsmasq_debug (2) - killing dnsmasq")
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()

    for line in out.splitlines():
        if 'dnsmasq' in line:
            pid = int(line.split(None, 1)[0])
            os.kill(pid, signal.SIGKILL)

    # Get the config
    dnsmasq_get_config()

    # Start the dnsmasq process
    dnsmasq_start_process()



#------------------ main() ----------------
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

    dnsmasq_init(remote)

    ovs.daemon.daemonize()

    ovs.unixctl.command_register("exit", "", 0, 0, unixctl_exit, None)
    error, unixctl_server = ovs.unixctl.server.UnixctlServer.create(None)

    if error:
        ovs.util.ovs_fatal(error, "Dnsmasq_helper: could not create "
                                  "unix-ctl server", vlog)

    while dnsmasq_started == False:
        dnsmasq_run()
        sleep(2)

    seqno = idl.change_seqno    # Sequence number when we last processed the db

    exiting = False
    while not exiting:

        unixctl_server.run()

        if exiting:
            break;

        if seqno == idl.change_seqno:
            poller = ovs.poller.Poller()
            unixctl_server.wait(poller)
            idl.wait(poller)
            poller.block()

        idl.run() # Better reload the tables

        vlog.dbg("dnsmasq_debug main - seqno change from %d to %d " \
                     % (seqno, idl.change_seqno))
        if seqno != idl.change_seqno:
            dnsmasq_restart()
            seqno = idl.change_seqno

    #Daemon Exit
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
