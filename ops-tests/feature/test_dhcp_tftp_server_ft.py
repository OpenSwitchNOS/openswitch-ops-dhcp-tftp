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

from pytest import mark
from time import sleep

TOPOLOGY = """
#                +--------+
#+--------+      |        |
#|  ops1  <------>  hs1   |
#+--------+      |        |
#                +--------+

# Nodes
[type=openswitch name="OpenSwitch 1"] ops1
[type=host name="Host 1"] hs1

# Links
ops1:1 -- hs1:eth1
"""

PATH = '/tmp/'
FILE_NAME = 'tftp_test.txt'


def setup_topo(topology):
    """
    Build a topology of one switch and one host. Connect the host to the
    switch. Assign an IP to the switch port and host so the host can ping
    the switch.
    """

    hs1 = topology.get('hs1')
    ops1 = topology.get('ops1')

    assert ops1 is not None
    assert hs1 is not None

    # Configure switch interface
    with ops1.libs.vtysh.ConfigInterface('1') as ctx:
        ctx.no_shutdown()
        ctx.ip_address("10.0.0.1/8")

    # Configure host interfaces
    hs1.libs.ip.interface('eth1', addr='10.0.0.2/8', up=True)


def enable_tftp_server(ops1, step):
    step("### Configure tftp-server in switch, and add a path ###")
    with ops1.libs.vtysh.ConfigTftpServer() as ctx:
        result_enable = ctx.enable()
        result_path = ctx.path(PATH)
        assert result_enable, 'Unable to enable TFTP-Server in the switch'
        assert result_path, 'Unable to set the path of TFTP-Server'
    step('### Verify tftp-server is configured ###')
    result = ops1.libs.vtysh.show_tftp_server()
    assert result['tftp_server'], 'The tftp-server is not enabled'
    assert result['tftp_server_file_path'], 'The tftp-server path is not set'


def create_file(ops1, step):
    step("### Creating a new file ###")
    ops1('echo \"TFTP test file\" > {0}{1}'.format(
        PATH, FILE_NAME),
        'bash')


def copy_tftp_file(ops1, hs1, step):
    step("### Download file from client by tftp ###")

    result = hs1("tftp -v 10.0.0.1 -m binary -c get {0}".format(FILE_NAME))
    assert "Received" in result, "TFTP file transfer failed"
    output = hs1("ls | grep {0}".format(FILE_NAME))
    assert FILE_NAME in output, "TFTP file copy to client failed"
    hs1("rm -rf {0}".format(FILE_NAME))
    ops1("rm -rf {0}{1}".format(PATH, FILE_NAME), 'bash')
    step("### TFTP-Server was verified successfully ###")


@mark.platform_incompatible(['docker'])
def test_tftp_server(topology, step):
    setup_topo(topology)

    step('### Waiting 5 seconds for OPS DOCKER to stabilize ###')
    sleep(5)

    hs1 = topology.get('hs1')
    ops1 = topology.get('ops1')

    enable_tftp_server(ops1, step)
    create_file(ops1, step)
    copy_tftp_file(ops1, hs1, step)
