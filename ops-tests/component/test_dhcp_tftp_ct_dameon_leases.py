# Copyright (C) 2016 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from time import sleep
from pytest import mark


TOPOLOGY = """
#
# +-------+
# |  sw1  |
# +-------+
#

# Nodes
[type=openswitch name="Switch 1"] sw1
"""


@mark.gate
def test_vtysh_dhcp_tftp(topology, step):
    sw1 = topology.get('sw1')

    assert sw1 is not None

    step('### Test to add DHCP dynamic configurations ###')
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1("range test-range start-ip-address 10.0.0.1 end-ip-address 10.0.0.254 "
        "netmask 255.0.0.0 match tags tag1,tag2,tag3 "
        "set tag test-tag broadcast 10.255.255.255 lease-duration 60")

    dump = sw1("do show dhcp-server")
    assert "10.0.0.1" in dump and "10.0.0.254" in dump and \
        "255.0.0.0" in dump and "tag1,tag2,tag3" in dump and \
        "tag" in dump and "10.255.255.255" in dump and "60" in dump

    sleep(20)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "10.0.0.1" in dump_bash and "10.0.0.254" in dump_bash and \
        "255.0.0.0" in dump_bash and "tag1" in dump_bash and \
        "tag2" in dump_bash and "tag3" in dump_bash and "tag" in \
        dump_bash and "10.255.255.255" in dump_bash and "60" in dump_bash

    step('### Test to add DHCP static configuration ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1('static 10.0.0.100 match-mac-addresses aa:bb:cc:dd:ee:ff '
        'set tags tag1,tag2,tag3 lease-duration 60')

    dump = sw1("do show dhcp-server")
    assert "10.0.0.100" in dump and "aa:bb:cc:dd:ee:ff" in dump \
        and "tag1,tag2,tag3" in dump and "60" in dump

    sleep(15)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "10.0.0.100" in dump_bash and "aa:bb:cc:dd:ee:ff" in dump_bash \
        and "tag1" and "tag2" and "tag3" in dump_bash and "60" in dump_bash

    step('### Test to add DHCP Options using option name ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1("option set option-name Router option-value 10.11.12.1 "
        "match tags opt1,opt2,opt3")

    dump = sw1("do show dhcp-server")
    assert "Router" in dump and "10.11.12.1" in dump and "False" in dump \
        and "opt1,opt2,opt3" in dump

    sleep(15)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "option:Router" in dump_bash and "10.11.12.1" in dump_bash and \
        "opt1" and "opt2" and "opt3" in dump_bash

    step('### Test to add DHCP Options using option number ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1("option set option-number 3 option-value 10.10.10.1 "
        "match tags tag4,tag5,tag6")

    dump = sw1("do show dhcp-server")
    assert "3" in dump and "10.10.10.1" in dump and "False" in dump and \
        "tag4,tag5,tag6" in dump

    sleep(20)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "3" in dump_bash and "10.10.10.1" in dump_bash and "tag4" and \
        "tag5" and "tag6" in dump_bash

    step('### Test to add DHCP Match using option name ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1("match set tag ops_match_name match-option-name Router "
        "match-option-value 10.20.10.1")

    dump = sw1("do show dhcp-server")
    assert "Router" in dump and "10.20.10.1" in dump and "ops_match_name" \
        in dump

    sleep(20)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "Router" in dump_bash and "10.20.10.1" in dump_bash and \
        "ops_match_name" in dump_bash

    step('### Test to add DHCP Match using option number ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1("match set tag ops_match_num match-option-number 3 "
        "match-option-value 10.20.20.10")

    dump = sw1("do show dhcp-server")
    assert "3" in dump and "10.20.20.10" in dump and "ops_match_num" in dump

    sleep(20)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "3" in dump_bash and "10.20.20.10" in dump_bash and \
        "ops_match_num" in dump_bash

    step('###  Test to add DHCP bootp configurations ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1("boot set file /tmp/testfile match tag ops_bootp")

    dump = sw1("do show dhcp-server")
    assert "/tmp/testfile" in dump and "ops_bootp" in dump

    sleep(20)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "/tmp/testfile" in dump_bash and "ops_bootp" in dump_bash

    step('### Test to delete DHCP dynamic configurations ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1("no range test-range start-ip-address 10.0.0.1 end-ip-address "
        "10.0.0.254 netmask 255.0.0.0 match tags tag1,tag2,tag3 "
        " set tag test-tag broadcast 10.255.255.255 lease-duration 60")

    dump = sw1("do show dhcp-server")
    range_created = False
    if "test-range" in dump and "10.0.0.1" in dump and \
        "10.0.0.254" in dump and "255.0.0.0" in dump and \
        "tag1,tag2,tag3" in dump and "tag" in dump and \
            "10.255.255.255" in dump and "60" in dump:
            range_created = True
    assert range_created is False

    sleep(20)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    range_in_use = False
    if "10.0.0.1" in dump_bash and "10.0.0.254" in dump_bash and \
        "255.0.0.0" in dump_bash and "tag1,tag2,tag3" in dump_bash  \
        and "tag" in dump_bash and "10.255.255.255" in dump_bash and \
            ",60" in dump_bash:
            range_in_use = True
    assert range_in_use is False

    step('### Test to delete DHCP static configuration ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1("no static 10.0.0.100 match-mac-addresses aa:bb:cc:dd:ee:ff "
        "set tags tag1,tag2,tag3 match-client-id testid "
        "match-client-hostname testname lease-duration 60")

    dump = sw1("do show dhcp-server")
    assert "10.0.0.100" not in dump and "aa:bb:cc:dd:ee:ff" not in dump \
        and "testid" not in dump and "tag1,tag2,tag3" not in dump and \
        "testname" not in dump and "60" not in dump

    sleep(20)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "10.0.0.100" not in dump_bash and "aa:bb:cc:dd:ee:ff" not in \
        dump_bash and "testid" not in dump_bash and "tag1,tag2,tag3" not \
        in dump_bash and "testname" not in dump_bash and ",60" not in \
        dump_bash

    step('### Test to delete DHCP Option using option name ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1("no option set option-name Router option-value 10.11.12.1 "
        "match tags opt1,opt2,opt3")

    dump = sw1("do show dhcp-server")
    option_created = False
    if "Router" in dump and "10.11.12.1" in dump and "False" \
            in dump and "opt1,opt2,opt3" in dump:
            option_created = True
    assert option_created is False

    sleep(20)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    option_in_use = False
    if "Router" in dump and "10.11.12.1" in dump \
            in dump and "opt1,opt2,opt3" in dump:
            option_in_use = True
    assert option_in_use is False

    step('### Test to delete DHCP Option using option number ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1("no option set option-number 3 option-value 10.10.10.1 "
        "match tags tag4,tag5,tag6")

    dump = sw1("do show dhcp-server")
    option_created = False
    if "3" in dump and "10.10.10.1" in dump and "False" in \
            dump and "tag4,tag5,tag6" in dump:
            option_created = True
    assert option_created is False

    sleep(20)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    option_in_use = False
    if "3" in dump_bash and "10.10.10.1" in dump_bash and \
            "tag4,tag5,tag6" in dump_bash:
            option_in_use = True
    assert option_in_use is False

    step('### Test to delete DHCP match using option name ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1("no match set tag ops_match_name match-option-name Router "
        "match-option-value 10.20.10.1")

    dump = sw1("do show dhcp-server")
    assert "Router" not in dump and "10.20.10.1" not in dump and \
        "ops_match_name" not in dump

    sleep(20)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "Router" not in dump and "10.20.10.1" not in dump and \
        "ops_match_name" not in dump

    step('### Test to delete DHCP match using option number ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1("no match set tag ops_match_num match-option-number 3 "
        "match-option-value 10.20.20.10")

    dump = sw1("do show dhcp-server")
    assert "3" not in dump and "10.20.20.10" not in dump and \
        "ops_match_num" not in dump

    sleep(20)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "3" not in dump and "10.20.20.10" not in dump and \
        "ops_match_num" not in dump

    step('### Test to delete DHCP bootp configuration ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1('dhcp-server')
    sw1("no boot set file /tmp/testfile match tag ops_bootp")

    dump = sw1("do show dhcp-server")
    assert "/tmp/testfile" not in dump and "ops_bootp" not in dump

    sleep(20)
    dump_bash = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "/tmp/testfile" not in dump_bash and "ops_bootp" not \
        in dump_bash

    step('### Test to enable tftp server ###')
    # Changing vtysh context because bash command set it back to default
    # Remove unnecesary command line 'exit'
    sw1('configure terminal')
    sw1("tftp-server")
    sw1('enable')
    dump = sw1("do show tftp-server")
    assert "TFTP server : Enabled" in dump

    sleep(20)
    dump = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "--enable-tftp" in dump

    step('### Test to enable tftp server secure mode ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1("tftp-server")
    sw1("secure-mode")
    dump = sw1("do show tftp-server")
    assert "TFTP server secure mode : Enabled" in dump

    sleep(20)
    dump = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "--tftp-secure" in dump

    step('### Test to add tftp path ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1("tftp-server")
    sw1("path /tmp/")
    dump = sw1("do show tftp-server")
    assert "TFTP server file path : /tmp/" in dump

    sleep(20)
    dump = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "--tftp-root=/tmp/" in dump

    step('### Test to disable tftp server ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1("tftp-server")
    sw1("no enable")
    dump = sw1("do show tftp-server")
    assert "TFTP server : Disabled" in dump

    sleep(20)
    dump = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "--enable-tftp" not in dump

    step('### Test to disable tftp server secure mode ###')
    # Changing vtysh context because bash command set it back to default
    sw1('configure terminal')
    sw1("tftp-server")
    sw1("no secure-mode")
    sw1('end')
    dump = sw1("show tftp-server")
    assert "TFTP server secure mode : Disabled" in dump

    sleep(20)
    dump = sw1("ps -ef | grep dnsmasq", shell='bash')
    assert "--tftp-secure" not in dump

    step('### Test to add DHCP leases information ###')
    sw1("export DNSMASQ_LEASE_EXPIRES=1440976224", shell='bash')
    sw1("dhcp_leases add 11:22:33:44:55:66 10.0.0.100 test_s1",
        shell='bash')
    # Removing do from command since bash command reseted vtysh context
    dump = sw1("show dhcp-server leases")
    assert "11:22:33:44:55:66" in dump and "10.0.0.100" in dump and \
        "test_s1" in dump

    step('### Test to modify DHCP leases information ###')
    sw1("export DNSMASQ_LEASE_EXPIRES=1440976224", shell='bash')
    sw1("dhcp_leases old 11:22:33:44:55:66 20.0.0.200 test_s1_new",
        shell='bash')
    dump = sw1("show dhcp-server leases")
    assert "11:22:33:44:55:66" in dump and "20.0.0.200" in dump and \
        "test_s1_new" in dump

    step('### Test to delete DHCP leases information ###')
    sw1("export DNSMASQ_LEASE_EXPIRES=1440976224", shell='bash')
    sw1("dhcp_leases del 11:22:33:44:55:66 20.0.0.200 test_s1_new",
        shell='bash')
    dump = sw1("show dhcp-server leases")
    assert "11:22:33:44:55:66" not in dump and "20.0.0.200" not in \
        dump and "test_s1_new" not in dump

    step('### Test to add DHCP v6 leases information ###')
    sw1("export DNSMASQ_LEASE_EXPIRES=1440976224", shell='bash')
    sw1("dhcp_leases add \
        01:02:03:04:05:06:07:08:09:10:11:12:13:14:15:16:17:18:19:20 \
        20:1::1:241 test_v6_s1",
        shell='bash')
    dump = sw1("show dhcp-server leases")
    assert "01:02:03:04:05:06:07:08:09:10:11:12:13:14:15:16:17:18:19:20" \
         in dump and "20:1::1:241" in dump and \
        "test_v6_s1" in dump

    step('### Test to modify DHCP v6 leases information ###')
    sw1("export DNSMASQ_LEASE_EXPIRES=1440976224", shell='bash')
    sw1("dhcp_leases old \
        01:02:03:04:05:06:07:08:09:10:11:12:13:14:15:16:17:18:19:20 \
        20:1::1:242 test_v6_s1_new",
        shell='bash')
    dump = sw1("show dhcp-server leases")
    assert "01:02:03:04:05:06:07:08:09:10:11:12:13:14:15:16:17:18:19:20" \
        in dump and "20:1::1:242" in dump and \
        "test_v6_s1_new" in dump

    step('### Test to delete DHCP v6 leases information ###')
    sw1("export DNSMASQ_LEASE_EXPIRES=1440976224", shell='bash')
    sw1("dhcp_leases del \
        01:02:03:04:05:06:07:08:09:10:11:12:13:14:15:16:17:18:19:20 \
        20:1::1:242 test_v6_s1_new",
        shell='bash')
    dump = sw1("show dhcp-server leases")
    assert "01:02:03:04:05:06:07:08:09:10:11:12:13:14:15:16:17:18:19:20" \
        not in dump and "20:1::1:242" not in \
        dump and "test_v6_s1_new" not in dump

    step('### Test to clear all DHCP server leases ###')
    sw1("export DNSMASQ_LEASE_EXPIRES=1440976224", shell='bash')
    sw1("dhcp_leases add 11:22:33:44:55:66 10.0.0.100 test_s1", shell='bash')
    sw1("dhcp_leases add 21:22:33:44:55:66 10.0.0.200 test_s2", shell='bash')
    sw1("configure terminal")
    sw1("dhcp-server")
    sw1("clear dhcp-server leases")
    dump = sw1("do show dhcp-server leases")
    assert "11:22:33:44:55:66" not in dump and "10.0.0.100" not in dump and \
           "test_s1" not in dump and "21:22:33:44:55:66" not in dump and \
           "10.0.0.200" not in dump and "test_s2" not in dump
