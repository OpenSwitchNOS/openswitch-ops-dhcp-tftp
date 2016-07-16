# Copyright (C) 2016 Hewlett Packard Enterprise Development LP
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# The purpose of this test is to test DHCP server address lease
# configurations for static allocations and verify the
# allocations in OVSDB and DHCP client interface.

# For this test, we need 2 hosts connected to a switch
# which start exchanging DHCP messages.
#
# S1 [interface 1]<--->[interface 1] H1
# S1 [interface 2]<--->[interface 2] H2

from pytest import mark

TOPOLOGY = """
#
# +-------+                  +-------+
# |       |     +---v---+    |       |
# |  hs1  <----->  sw1  <---->  hs2  |
# |       |     +-------+    |       |
# +-------+                  +-------+
#

# Nodes
[type=openswitch name="Switch 1"] sw1
[type=host name="host 1"] h1
[type=host name="host 2"] h2

# Links
sw1:if01 -- h1:if01
sw1:if02 -- h2:if01
"""

host1_pool = "host1"
host2_pool = "host2"
start_ipv4_address_pool1 = "10.0.0.1"
end_ipv4_address_pool1 = "10.0.0.100"
start_ipv4_address_pool2 = "20.0.0.1"
end_ipv4_address_pool2 = "20.0.0.100"
host1_mac_address = ""
host2_mac_address = ""
host1_static_ip_address = "10.0.0.5"
host2_static_ip_address = "20.0.0.5"

def get_mac_address_of_hosts(h1, h2):
    print('\### Acquiring the MAC address of the hosts ###\n')

    # Parse the "ifconfig" outputs for interfaces
    # h1-eth0 and h2-eth0 for hosts 1 and 2
    # respectively and save the values for MAC
    # addresses into variables above

    ifconfigmacaddridx = 4
    ifconfigmacaddrlinenum = 0
    global host1_mac_address
    global host2_mac_address

    h1p1 = h1.ports['if01']
    h2p1 = h2.ports['if01']

    dump = h1("ifconfig {h1p1}".format(**locals()))
    count = 0
    lines = dump.split('\n')
    for line in lines:
        if count == ifconfigmacaddrlinenum:
            outstr = line.split()
            print(outstr)
            host1_mac_address = outstr[ifconfigmacaddridx]
        count = count + 1

    dump = h2("ifconfig {h2p1}".format(**locals()))
    lines = dump.split('\n')
    count = 0
    for line in lines:
        if count == ifconfigmacaddrlinenum:
            outstr = line.split()
            host2_mac_address = outstr[ifconfigmacaddridx]
        count = count +1


def configure(sw1):
    print('\n### Test DHCP server static IPV4 configuration ###\n')
    print('\n### Configuring static IPV4 address allocation ###\n')

    sw1p1 = sw1.ports['if01']
    sw1p2 = sw1.ports['if02']

    # Configure switch s1
    # Configure interface 1 on switch s1
    with sw1.libs.vtysh.ConfigInterface(sw1p1) as ctx:
        ctx.no_shutdown()
        ctx.ip_address("10.0.10.1/8")
        ctx.ipv6_address("2000::1/120")

    # Configure interface 2 on switch s1
    with sw1.libs.vtysh.ConfigInterface(sw1p2) as ctx:
        ctx.no_shutdown()
        ctx.ip_address("20.0.0.1/8")
        ctx.ipv6_address("2001::1/120")

    sw1("configure terminal")
    sw1("dhcp-server")
    sw1("range host1 start-ip-address %s end-ip-address %s"
        % (start_ipv4_address_pool1, end_ipv4_address_pool1))

    sw1("range host2 start-ip-address %s end-ip-address %s"
        % (start_ipv4_address_pool2, end_ipv4_address_pool2))

    sw1("static %s match-mac-addresses %s"
        % (host1_static_ip_address, host1_mac_address))

    sw1("static %s match-mac-addresses %s"
        % (host2_static_ip_address, host2_mac_address))

    sw1("end")


def dhcp_server_static_ipv4_config(sw1):
    print('\n### Verify DHCP server static ipv4 config in db ###\n')

    # Parse "show dhcp-server" output.
    # This section will have all the DHCP server
    # range and static configuration entries.
    # Then parse line by line to match the contents

    dump = sw1.libs.vtysh.show_dhcp_server()

    # Verifying the dhcp server range configuration
    assert (host1_pool == dump['pools'][1]['pool_name'] or
            host1_pool == dump['pools'][0]['pool_name']) and \
        (start_ipv4_address_pool1 == dump['pools'][1]['start_ip'] or
         start_ipv4_address_pool1 == dump['pools'][0]['start_ip']) and \
        (end_ipv4_address_pool1 == dump['pools'][1]['end_ip'] or
         end_ipv4_address_pool1 == dump['pools'][0]['end_ip'])
    assert (host2_pool == dump['pools'][0]['pool_name'] or
            host2_pool == dump['pools'][1]['pool_name']) and \
        (start_ipv4_address_pool2 == dump['pools'][0]['start_ip'] or
         start_ipv4_address_pool2 == dump['pools'][1]['start_ip']) and \
        (end_ipv4_address_pool2 == dump['pools'][0]['end_ip'] or
         end_ipv4_address_pool2 == dump['pools'][1]['end_ip'])

    # Verifying the dhcp server static configuration
    assert (host1_mac_address == dump['static'][1]['mac_address'] or
            host1_mac_address == dump['static'][0]['mac_address']) and \
            (host1_static_ip_address == dump['static'][1]['static_ip'] or
             host1_static_ip_address == dump['static'][0]['static_ip'])
    assert (host2_mac_address == dump['static'][1]['mac_address'] or
            host2_mac_address == dump['static'][0]['mac_address']) and \
            (host2_static_ip_address == dump['static'][1]['static_ip'] or
             host2_static_ip_address == dump['static'][0]['static_ip'])

def configure_dhcp_client(h1, h2):
    print('\n### Configure DHCP clients for '
          'static IPV4 address in db ###\n')
    h1p1 = h1.ports['if01']
    h2p1 = h2.ports['if01']

    h1("sed -i 's/#timeout 60/timeout 30/g' /etc/dhcp/dhclient.conf")

    h1("ifconfig -a")
    h1("ip addr del 10.0.0.1/8 dev {h1p1}".format(**locals()))
    h1("dhclient {h1p1}".format(**locals()))
    h1("sed -i 's/timeout 30/#timeout 60/g' /etc/dhcp/dhclient.conf")

    h2("sed -i 's/#timeout 60/timeout 30/g' /etc/dhcp/dhclient.conf")
    h2("ifconfig -a")
    h2("ip addr del 10.0.0.2/8 dev {h2p1}".format(**locals()))
    h2("dhclient {h2p1}".format(**locals()))
    h2("sed -i 's/timeout 30/#timeout 60/g' /etc/dhcp/dhclient.conf")


def dhcp_client_static_ipv4_address_config(h1, h2, sw1):
    print('\n### Verify DHCP clients h1 and h2 '
          'static IPV4 address config in db ###\n')
    h1p1 = h1.ports['if01']
    h2p1 = h2.ports['if01']

    ifconfighost1ipv4addr = ""
    ifconfighost2ipv4addr = ""
    ifconfigipv4prefixpattern = "inet addr:"
    ifconfigipv4addridx = 1
    ifconfigipv4addrlinenum = 1

    # Parse the "ifconfig" outputs for interfaces
    # h1-eth0 and h2-eth0 for hosts 1 and 2
    # respectively and save the values for IP
    # addresses into variables above
    dump = h1("ifconfig {h1p1}".format(**locals()))
    host_1_ip_address = dump.split("\n")[1].split()[1][5:]
    lines = dump.split('\n')
    count = 0
    for line in lines:
        if count == ifconfigipv4addrlinenum:
            outstr = line.split()
            ifconfighost1ipv4addrtemp1 = outstr[ifconfigipv4addridx]
            ifconfighost1ipv4addrtemp2 = ifconfighost1ipv4addrtemp1.split(':')
            ifconfighost1ipv4addr = ifconfighost1ipv4addrtemp2[1]
        count = count + 1

    dump = h2("ifconfig {h2p1}".format(**locals()))
    host_2_ip_address = dump.split("\n")[1].split()[1][5:]
    lines = dump.split('\n')
    count = 0
    for line in lines:
        if count == ifconfigipv4addrlinenum:
            outstr = line.split()
            ifconfighost2ipv4addrtemp1 = outstr[ifconfigipv4addridx]
            ifconfighost2ipv4addrtemp2 = ifconfighost2ipv4addrtemp1.split(':')
            ifconfighost2ipv4addr = ifconfighost2ipv4addrtemp2[1]
        count = count + 1

    # Parse the "show dhcp-server leases" output
    # and verify if the values for interfaces
    # h1-eth0 and h2-eth0 for hosts
    # 1 and 2 respectively are present in the lease dB
    dump = sw1.libs.vtysh.show_dhcp_server_leases()
    if host1_mac_address == dump[host_1_ip_address]['mac_address']:
        dhcpipv4addrhost1 = dump[host_1_ip_address]['ip_address']
        assert dhcpipv4addrhost1 == ifconfighost1ipv4addr
    elif host1_mac_address == dump[host_2_ip_address]['mac_address']:
        dhcpipv4addrhost2 = dump[host_2_ip_address]['ip_address']
        assert dhcpipv4addrhost2 == ifconfighost2ipv4addr


@mark.gate
def test_ft_static_dhcp_tftp_commands(topology, step):
    sw1 = topology.get('sw1')
    h1 = topology.get('h1')
    h2 = topology.get('h2')

    assert sw1 is not None
    assert h1 is not None
    assert h2 is not None

    step('\n########## Test DHCP server static '
         'IPV4 configuration ##########\n')
    get_mac_address_of_hosts(h1, h2)
    configure(sw1)
    dhcp_server_static_ipv4_config(sw1)
    configure_dhcp_client(h1, h2)
    dhcp_client_static_ipv4_address_config(h1, h2, sw1)
