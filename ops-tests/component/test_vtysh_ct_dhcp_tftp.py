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

TOPOLOGY = """
#
# +-------+
# |  sw1  |
# +-------+
#

# Nodes
[type=openswitch name="Switch 1"] sw1
"""


def test_dhcp_tftp(topology, step):  # noqa

    sw1 = topology.get('sw1')

    assert sw1 is not None

    step("### Test to add DHCP dynamic configurations ###")
    range_created = False
    sw1('configure terminal'.format(**locals()))
    sw1('dhcp-server'.format(**locals()))
    sw1('range test-range start-ip-address 10.0.0.1 '
        'end-ip-address 10.255.255.254 '
        'netmask 255.0.0.0 match tags tag1,tag2,tag3 '
        'set tag test-tag broadcast 10.255.255.255 '
        'lease-duration 60'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
            if "test-range" in line \
                and "10.0.0.1" in line \
                and "10.255.255.254" in line and "255.0.0.0" in line \
                and "tag1,tag2,tag3" in line and "test-tag" in line \
                    and "10.255.255.255" in line and "60" in line:
                    range_created = True

    assert range_created, 'Test to add DHCP Dynamic configuration' \
                          ' failed for "show dhcp-server" output' \
                          ' -FAILED!'

    range_created = False
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "test-range" in line \
            and "10.0.0.1" in line \
            and "10.255.255.254" in line and "255.0.0.0" in line \
            and "tag1,tag2,tag3" in line and "test-tag" in line \
                and "10.255.255.255" in line:
                range_created = True

    assert range_created, 'Test to add DHCP Dynamic configuration' \
                          ' failed for "show running" output' \
                          ' -FAILED!'

    step("### Test to add DHCP dynamic ipv6 configurations ###")
    range_created = False
    sw1('range range-ipv6 start-ip-address 2001:cdba::3257:9652 '
        'end-ip-address 2001:cdba::3257:9655 '
        'prefix-len 64 '
        'match tags v6tag1,v6tag2,v6tag3 '
        'set tag v6-stag '
        'lease-duration 60'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
            if "range-ipv6" in line \
                and "2001:cdba::3257:9652" in line \
                and "2001:cdba::3257:9655" in line and "64" in line \
                and "v6tag1,v6tag2,v6tag3" in line and "v6-stag" in line \
                    and "60" in line:
                    range_created = True

    assert range_created, 'Test to add DHCP Dynamic ipv6 ' \
                          'configuration failed for ' \
                          '"show dhcp-server" output -FAILED!'

    range_created = False
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "range-ipv6" in line \
            and "2001:cdba::3257:9652" in line \
            and "2001:cdba::3257:9655" in line and "64" in line \
                and "v6tag1,v6tag2,v6tag3" in line and "v6-stag" in line:
                range_created = True

    assert range_created, 'Test to add DHCP Dynamic ipv6 '\
                          'configuration failed for ' \
                          '"show running-config" output- FAILED!'

    step("### Test to check range validation ###")
    ret = sw1('range test-range start-ip-address 300.300.300.300 '
              'end-ip-address 192.168.0.254 '
              'netmask 255.255.255.0 match tags tag1,tag2,tag3 '
              'set tag test-tag broadcast 192.168.0.255 '
              'lease-duration 60'.format(**locals()))

    assert '% Unknown command.' in ret, 'Start IP address validation failed'

    ret = sw1('range test-range start-ip-address 192.168.0.1  '
              'end-ip-address 300.300.300.300 '
              'netmask 255.255.255.0 match tags tag1,tag2,tag3 '
              'set tag test-tag broadcast 192.168.0.255 '
              'lease-duration 60'.format(**locals()))

    assert '% Unknown command.' in ret, 'End IP address validation failed'

    ret = sw1('range test-range start-ip-address 192.168.0.1 '
              'end-ip-address 192.168.0.254 '
              'netmask 127.0.0.1 match tags tag1,tag2,tag3 '
              'set tag test-tag broadcast 192.168.0.255 '
              'lease-duration 60'.format(**locals()))

    assert '127.0.0.1 is invalid' in ret, 'Netmask validation failed'

    ret = sw1('range testrange start-ip-address 2001:cdba::3257:9642 '
              'end-ip-address 2001:cdba::3257:9648 '
              'netmask 255.255.255.0 match tags tag1,tag2,tag3 '
              'set tag test-tag broadcast 192.168.0.255 '
              'lease-duration 60'.format(**locals()))

    assert 'Error : netmask configuration not allowed for IPv6' in ret, \
           'netmask ipv6 validation failed'

    ret = sw1('range test-range start-ip-address 192.168.0.1 '
              'end-ip-address 10.0.0.1 '
              'netmask 255.255.255.0 match tags tag1,tag2,tag3 '
              'set tag test-tag broadcast 192.168.0.255 '
              'lease-duration 60'.format(**locals()))

    assert 'Invalid IP address range' in ret, \
           'ip address range validation failed'

    ret = sw1('range test-range start-ip-address 192.168.0.1 '
              'end-ip-address 192.168.0.254 '
              'netmask 255.255.255.0 match tags tag1,tag2,tag3 '
              'set tag test-tag broadcast 300.300.300.300 '
              'lease-duration 60'.format(**locals()))

    assert '% Unknown command.' in ret, 'broadcast address validation failed'

    ret = sw1('range test-range start-ip-address 192.168.0.1 '
              'end-ip-address 192.168.0.254 '
              'netmask 255.255.255.0 '
              'match tags tag1,tag2,tag3 '
              'set tag test-tag broadcast 10.0.0.255 '
              'lease-duration 60'.format(**locals()))

    assert '10.0.0.255 is invalid' in ret, \
           'broadcast address ipv6 validation failed'

    ret = sw1('range test-range start-ip-address 192.168.0.1 '
              'end-ip-address 192.168.0.254 '
              'match tags tag1,this-tag-length-greater-than-15,tag3 '
              'set tag test-tag broadcast 192.168.0.255 '
              'lease-duration 60'.format(**locals()))

    assert 'this-tag-length-greater-than-15' in ret, \
           'match tags validation failed'

    ret = sw1('range test-range start-ip-address 192.168.0.1 '
              'end-ip-address 192.168.0.254 '
              'match tags tag1,tag2,tag3 '
              'set tag test-this-tag-greater-than-15 '
              'broadcast 192.168.0.1 '
              'lease-duration 60'.format(**locals()))

    assert 'test-this-tag-greater-than-15' in ret, \
           'set tag validation failed'

    ret = sw1('range test-range start-ip-address 192.168.0.1 '
              'end-ip-address 192.168.0.254 '
              'match tags tag1,tag2,tag3 '
              'set tag test-tag broadcast 192.168.0.1 '
              'lease-duration 120000'.format(**locals()))

    assert '% Unknown command.' in ret, 'set tag validation failed'

    step("### Test to add DHCP static configuration ###")
    static_created = False
    sw1('static 192.168.0.2 '
        'match-mac-addresses aa:bb:cc:dd:ee:ff '
        'set tags tag4,tag5,tag6 '
        'match-client-id testid '
        'match-client-hostname testname '
        'lease-duration 60'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "192.168.0.2" in line \
            and "aa:bb:cc:dd:ee:ff" in line \
            and "testid" in line \
            and "tag4,tag5,tag6" in line \
            and "testname" in line \
                and "60" in line:
                static_created = True

    assert static_created, 'Test to add DHCP static configuration ' \
                           'failed for "show dhcp-server" output ' \
                           '-FAILED!'

    static_created = False
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "192.168.0.2" in line \
            and "aa:bb:cc:dd:ee:ff" in line \
            and "testid" in line \
            and "tag4,tag5,tag6" in line \
                and "testname" in line:
                static_created = True

    assert static_created, 'Test to add DHCP static configuration ' \
                           'failed for "show running-config" output ' \
                           '-FAILED!'

    step("### Test to add DHCP static ipv6 configuration ###")
    static_created = False
    sw1('static 2001:cdba::3257:9680 '
        'match-mac-addresses ae:bb:cc:dd:ee:ff '
        'set tags v6-stag1,v6-stag2,v6-stag3 '
        'match-client-id v6testid '
        'match-client-hostname v6testname '
        'lease-duration 60'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "2001:cdba::3257:9680" in line \
            and "ae:bb:cc:dd:ee:ff" in line \
            and "v6testid" in line \
            and "v6-stag1,v6-stag2,v6-stag3" in line \
                and "v6testname" in line:
                static_created = True

    assert static_created, 'Test to add DHCP static ipv6 ' \
                           'configuration failed for ' \
                           '"show dhcp-server" output ' \
                           '-FAILED!'

    static_created = False
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "2001:cdba::3257:9680" in line \
            and "ae:bb:cc:dd:ee:ff" in line \
            and "v6testid" in line \
            and "v6-stag1,v6-stag2,v6-stag3" in line \
                and "v6testname" in line:
                static_created = True

    assert static_created, 'Test to add DHCP static ipv6 ' \
                           'configuration failed for ' \
                           '"show running-config" output ' \
                           '-FAILED!'

    step("### Test to check range validation ###")
    ret = sw1('static 300.300.300.300 '
              'match-mac-addresses aa:bb:cc:dd:ee:ff '
              'set tags tag1,tag2,tag3 '
              'match-client-id testid '
              'match-client-hostname testname '
              'lease-duration 60'.format(**locals()))

    assert '% Unknown command.' in ret, \
           'static ip address validation failed'

    # Testing mac address validation
    ret = sw1('static 150.0.0.1 '
              'match-mac-addresses aabbccddeeff '
              'set tags tag1,tag2,tag3 '
              'match-client-id testid '
              'match-client-hostname testname '
              'lease-duration 60'.format(**locals()))

    assert 'aabbccddeeff is invalid' in ret, \
           'MAC address validation failed'

    # Testing set tags validation
    ret = sw1('static 150.0.0.1 '
              'match-mac-addresses aa:bb:cc:dd:ee:ff '
              'set tags '
              't1-tag-this-tag-length-greater-than-15,tag2,tag3 '
              'match-client-id testid '
              'match-client-hostname testname '
              'lease-duration 60'.format(**locals()))

    assert 't1-tag-this-tag-length-greater-than-15 is invalid' in ret, \
           'set tags validation failed'

    ret = sw1('static 150.0.0.1 '
              'match-mac-addresses aa:bb:cc:dd:ee:ff '
              'set tags tag1,tag2,tag3 '
              'match-client-id this-client-id-length-greater-than-15 '
              'match-client-hostname testname '
              'lease-duration 60'.format(**locals()))

    assert 'this-client-id-length-greater-than-15 is invalid' in ret, \
           'client-id validation failed'

    # Testing client-hostname validation
    ret = sw1('static 150.0.0.1 '
              'match-mac-addresses aa:bb:cc:dd:ee:ff '
              'set tags tag1,tag2,tag3 '
              'match-client-id testid '
              'match-client-hostname this-hostname-greater-than-15 '
              'lease-duration 60'.format(**locals()))

    assert 'this-hostname-greater-than-15 is invalid' in ret, \
           'client-hostname validation failed'

    step("### Test to add DHCP Option-name ###")
    sw1('option '
        'set option-name opt-name '
        'option-value 192.168.0.1 '
        'match tags mtag1,mtag2,mtag3'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "opt-name" in line \
            and "192.168.0.1" in line \
            and "False" in line \
                and "mtag1,mtag2,mtag3" in line:
                option_created = True

    assert option_created, 'Test to add DHCP Option-name ' \
                           'failed for "show dhcp-server" ' \
                           'output -FAILED!'

    option_created = False
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "opt-name" in line \
            and "192.168.0.1" in line \
                and "mtag1,mtag2,mtag3" in line:
                option_created = True

    assert option_created, 'Test to add DHCP Option-name ' \
                           'failed for "show running-config" ' \
                           'output -FAILED!'

    step("### Test to add DHCP Option-number ###")
    sw1('option '
        'set option-number 3 '
        'option-value 192.168.0.3 '
        'match tags mtag4,mtag5,mtag6'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "3" in line \
            and "192.168.0.3" in line \
            and "False" in line \
                and "mtag4,mtag5,mtag6" in line:
                option_created = True

    assert option_created, 'Test to add DHCP Option-number ' \
                           'failed for "show dhcp-server" ' \
                           'output -FAILED!'

    option_created = False
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "3" in line \
            and "192.168.0.3" in line \
                and "mtag4,mtag5,mtag6" in line:
                option_created = True

    assert option_created, 'Test to add DHCP Option-number ' \
                           'failed for "show running-config" ' \
                           'output -FAILED!'

    step("### Test to check DHCP Options using option number ###")
    ret = sw1('option '
              'set option-number 300 '
              'option-value 10.0.0.1 '
              'match tags tag1,tag2,tag3'.format(**locals()))

    assert '% Unknown command.' in ret, 'option-number validation failed'

    # Testing match tags validation
    ret = sw1('option '
              'set option-number 3 '
              'option-value 10.0.0.1 '
              'match tags '
              'tag1,option-name-greater-than-15,tag3'.format(**locals()))

    assert 'option-name-greater-than-15 is invalid' in ret, \
           'match tag validation failed'

    step("### Test to check DHCP Options using option name ###")
    ret = sw1('option '
              'set option-name set-option-name-greater-than-15 '
              'option-value 10.0.0.1 '
              'match tags tag1,tag2,tag3'.format(**locals()))

    assert 'set-option-name-greater-than-15 is invalid' in ret, \
           'option-name validation failed'

    # Testing match tags validation
    ret = sw1('option '
              'set option-name Router '
              'option-value 10.0.0.1 '
              'match tags '
              'match-option-name-greater-than-15,tag2,tag3'.format(**locals()))

    assert 'match-option-name-greater-than-15 is invalid' in ret, \
           'match tag validation failed'

    step("### Test to add DHCP match number ###")
    sw1('match '
        'set tag stag '
        'match-option-number 4 '
        'match-option-value 192.168.0.4'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "4" in line \
            and "192.168.0.4" in line \
                and "stag" in line:
                match_created = True

    assert match_created, 'Test to add DHCP match number ' \
                          'failed for "show dhcp-server" ' \
                          'output -FAILED!'

    match_created = False
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "4" in line \
            and "192.168.0.4" in line \
                and "stag" in line:
                match_created = True

    assert match_created, 'Test to add DHCP match number ' \
                          'failed for "show running-config" ' \
                          'output -FAILED!'

    step("### Test to check DHCP Match using option number ###")
    ret = sw1('match '
              'set tag name-greater-than-15 '
              'match-option-number 3 '
              'match-option-value 10.0.0.1'.format(**locals()))

    assert 'name-greater-than-15 is invalid' in ret, \
           'match set tag validation failed'

    # Testing option number validation
    ret = sw1('match '
              'set tag test-tag '
              'match-option-number 300 '
              'match-option-value 10.0.0.1'.format(**locals()))

    assert '% Unknown command.' in ret, \
           'match option number validation failed'

    step("### Test to add DHCP match name ###")
    sw1('match '
        'set tag temp-mtag '
        'match-option-name temp-mname '
        'match-option-value 192.168.0.5'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "temp-mname" in line \
            and "192.168.0.5" in line \
                and "temp-mtag" in line:
                match_created = True

    assert match_created, 'Test to add DHCP match number ' \
                          'failed for "show dhcp-server" ' \
                          'output -FAILED!'

    match_created = False
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "temp-mname" in line \
            and "192.168.0.5" in line \
                and "temp-mtag" in line:
                match_created = True

    assert match_created, 'Test to add DHCP match number ' \
                          'failed for "show running-config" ' \
                          'output -FAILED!'

    step("### Test to check DHCP Match using option name ###")
    # Testing set tag validation
    ret = sw1('match '
              'set tag tag-greater-than-15 '
              'match-option-name tempname '
              'match-option-value 10.0.0.1'.format(**locals()))

    assert 'tag-greater-than-15 is invalid' in ret, \
           'match set tag validation failed'

    # Testing option number validation
    ret = sw1('match '
              'set tag test-tag '
              'match-option-name tag-name-greater-than-15 '
              'match-option-value 10.0.0.1'.format(**locals()))

    assert 'tag-name-greater-than-15 is invalid' in ret, \
           'match option name validation failed'

    step("### Test to add DHCP bootp ###")
    boot_created = False
    sw1('boot '
        'set file /tmp/testfile '
        'match tag boottag'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "/tmp/testfile" in line and "boottag" in line:
            boot_created = True

    assert boot_created, 'Test to add DHCP bootp ' \
                         'failed for "show dhcp-server" ' \
                         'output -FAILED!'

    boot_created = False
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "/tmp/testfile" in line and "boottag" in line:
            boot_created = True

    assert boot_created, 'Test to add DHCP bootp ' \
                         'failed for "show running-config" ' \
                         'output -FAILED!'

    step("### Test to check DHCP Bootp validation ###")
    # Testing set tag validation
    ret = sw1('boot '
              'set file /tmp/tmpfile '
              'match tag boot-tag-name-greater-than-15'.format(**locals()))

    assert 'boot-tag-name-greater-than-15 is invalid' in ret, \
           'Bootp match tag validation failed'

    sw1('exit'.format(**locals()))

    step("### Test to enable tftp server ###")
    tftp_enabled = False
    sw1('tftp-server'.format(**locals()))
    sw1('enable'.format(**locals()))

    dump = sw1('do show tftp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "TFTP server : Enabled" in line:
            tftp_enabled = True

    assert tftp_enabled, 'Test to enable tftp server ' \
                         'failed for "show tftp-server" ' \
                         'output -FAILED!'

    tftp_server_present = False
    prev_line = 0
    enable_present = False
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    i = 0
    for i, line in enumerate(lines):
        if "tftp-server" in line:
            tftp_server_present = True
            prev_line = i
        elif (prev_line + 1 == i) and (tftp_server_present):
            if "enable" in line:
                enable_present = True

    assert enable_present, 'Test to enable tftp server ' \
                           'failed for "show running-config" ' \
                           'output -FAILED!'

    step("### Test to enable tftp server ###")
    tftp_secure_enabled = False
    sw1('secure-mode'.format(**locals()))

    dump = sw1('do show tftp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "TFTP server secure mode : Enabled" in line:
            tftp_secure_enabled = True

    assert tftp_secure_enabled, 'Test to enable tftp server ' \
                                'secure  mode failed for ' \
                                '"show tftp-server" output -FAILED!'

    secure_mode_present = False
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "secure-mode" in line:
            secure_mode_present = True

    assert secure_mode_present, 'Test to enable tftp server ' \
                                'secure  mode failed for ' \
                                '"show running-config" output -FAILED!'

    step("### Test to add tftp path ###")
    tftp_path = False
    sw1('path /etc'.format(**locals()))

    dump = sw1('do show tftp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "TFTP server file path : /etc" in line:
            tftp_path = True

    assert tftp_path, 'Test to add tftp path ' \
                      'failed for "show tftp-server" ' \
                      'output -FAILED!'

    tftp_path_present = False
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "path /etc" in line:
            tftp_path_present = True

    assert tftp_path_present, 'Test to add tftp path ' \
                              'failed for "show running-config" ' \
                              'output -FAILED!'

    tftp_non_directory_path = False
    dump = sw1('path /var/lib/image.manifest'.format(**locals()))

    lines = dump.split('\n')
    for line in lines:
        if "The directory \"/var/lib/image.manifest\" does not exist. " \
           "Please configure a valid absolute path." in line:
            tftp_non_directory_path = True

    assert tftp_non_directory_path == True, 'Test to add tftp path failed ' \
                               'TFTP-server configured with invalid path'

    tftp_relative_path = False
    dump = sw1('path etc/testfile'.format(**locals()))

    lines = dump.split('\n')
    for line in lines:
        if "The directory \"etc/testfile\" does not exist. " \
           "Please configure a valid absolute path." in line:
            tftp_relative_path = True

    assert tftp_relative_path == True, 'Test to add tftp path failed ' \
                               'TFTP-server configured with invalid path'

    step("### Test to show dhcp server configuration ###")
    range_present = False
    static_present = False
    option_name = False
    option_number = False
    match_created = False
    boot_created = False
    show_success = False
    match_number = False

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "test-range" in line \
            and "10.0.0.1" in line \
            and "10.255.255.254" in line and "255.0.0.0" in line \
            and "tag1,tag2,tag3" in line and "test-tag" in line \
                and "10.255.255.255" in line and "60" in line:
                range_present = True

        if "192.168.0.2" in line \
            and "aa:bb:cc:dd:ee:ff" in line \
            and "testid" in line \
            and "tag4,tag5,tag6" in line \
            and "testname" in line \
                and "60" in line:
                static_present = True

        if "opt-name" in line \
            and "192.168.0.1" in line \
            and "False" in line \
                and "mtag1,mtag2,mtag3" in line:
                option_name = True

        if "3" in line \
            and "192.168.0.3" in line \
            and "False" in line \
                and "mtag4,mtag5,mtag6" in line:
                option_number = True

        if "4" in line \
            and "192.168.0.4" in line \
                and "stag" in line:
                match_number = True

        if "temp-mname" in line \
            and "192.168.0.5" in line \
                and "temp-mtag" in line:
                match_created = True

        if "/tmp/testfile" in line and "boottag" in line:
            boot_created = True

    if range_present is True \
        and static_present is True \
        and option_name is True \
        and option_number is True \
        and match_number is True \
        and match_created is True \
            and boot_created is True:
            show_success = True

    assert show_success, 'Test to show dhcp server ' \
                         'server configuration failed ' \
                         'for "show dhcp-server" output -FAILED'

    range_present = False
    static_present = False
    option_name = False
    option_number = False
    match_created = False
    boot_created = False
    show_success = False
    match_number = False

    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "test-range" in line \
            and "10.0.0.1" in line \
            and "10.255.255.254" in line and "255.0.0.0" in line \
            and "tag1,tag2,tag3" in line and "test-tag" in line \
                and "10.255.255.255" in line:
                range_present = True

        if "192.168.0.2" in line \
            and "aa:bb:cc:dd:ee:ff" in line \
            and "testid" in line \
            and "tag4,tag5,tag6" in line \
                and "testname" in line:
                static_present = True

        if "opt-name" in line \
            and "192.168.0.1" in line \
                and "mtag1,mtag2,mtag3" in line:
                option_name = True

        if "3" in line \
            and "192.168.0.3" in line \
                and "mtag4,mtag5,mtag6" in line:
                option_number = True

        if "4" in line \
            and "192.168.0.4" in line \
                and "stag" in line:
                match_number = True

        if "temp-mname" in line \
            and "192.168.0.5" in line \
                and "temp-mtag" in line:
                match_created = True

        if "/tmp/testfile" in line and "boottag" in line:
            boot_created = True

    if range_present is True \
        and static_present is True \
        and option_name is True \
        and option_number is True \
        and match_number is True \
        and match_created is True \
            and boot_created is True:
            show_success = True

    assert show_success, 'Test to show dhcp server ' \
                         'configuration failed for ' \
                         '"show running-config" output -FAILED!'

    step("### Test to show tftp server configuration ###")
    tftp_server = False
    tftp_secure = False
    tftp_path = False
    show_tftp = False

    dump = sw1('do show tftp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "TFTP server : Enabled" in line:
            tftp_server = True
        if "TFTP server secure mode : Enabled" in line:
            tftp_secure = True
        if "TFTP server file path : /etc" in line:
            tftp_path = True

    if tftp_server is True \
        and tftp_secure is True \
            and tftp_path is True:
            show_tftp = True

    assert show_tftp, 'Test to show tftp server ' \
                      'configuration failed for ' \
                      '"show tftp-server" output -FAILED'

    tftp_server_present = False
    prev_line = 0
    prev_line2 = 0
    prev_line3 = 0
    enable_present = False
    secure_mode_present = False
    tftp_path_present = False
    show_tftp = False
    i = 0
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for i, line in enumerate(lines):
        if "tftp-server" in line:
            tftp_server_present = True
            prev_line = i
        elif (prev_line + 1 == i) and tftp_server_present:
            if "enable" in line:
                enable_present = True
                prev_line2 = i
        elif (prev_line2 + 1 == i) and tftp_server_present \
                and enable_present:
            if "secure-mode" in line:
                secure_mode_present = True
                prev_line3 = i
        elif (prev_line3 + 1 == i) and tftp_server_present \
                and enable_present and secure_mode_present:
            if "path /etc" in line:
                tftp_path_present = True

    if tftp_server_present is True \
        and enable_present is True \
        and secure_mode_present is True \
            and tftp_path_present is True:
            show_tftp = True

    assert show_tftp, 'Test to tftp server ' \
                      'configuration failed for ' \
                      '"show running-config" output -FAILED!'

    step("### Test to disable tftp server ###")
    tftp_disabled = False
    sw1('no enable'.format(**locals()))
    dump = sw1('do show tftp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "TFTP server : Disabled" in line:
            tftp_disabled = True

    assert tftp_disabled, 'Test to disable tftp server ' \
                          'failed for "show tftp-server" ' \
                          'output -FAILED!'

    tftp_server_present = False
    enable_mode_present = False
    prev_line = 0
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for i, line in enumerate(lines):
        if "tftp-server" in line:
            tftp_server_present = True
            prev_line = i
        elif (i == prev_line+1) and tftp_server_present:
            if "enable" in line:
                enable_mode_present = True

    assert not enable_mode_present, 'Test to disable tftp server ' \
                                    'failed for "show running-"' \
                                    'config output -FAILED!'

    step("### Test to disable tftp server secure mode ###")
    tftp_secure_disabled = False
    sw1('no secure-mode'.format(**locals()))
    dump = sw1('do show tftp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "TFTP server secure mode : Disabled" in line:
            tftp_secure_disabled = True

    assert tftp_secure_disabled, 'Test to disable tftp server '\
                                 'secure mode failed for ' \
                                 '"show tftp-server" output -FAILED!'

    tftp_server_present = False
    secure_mode_present = False
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "tftp-server" in line:
            tftp_server_present = True
        elif tftp_server_present:
            if "secure-mode" in line:
                secure_mode_present = True

    assert not secure_mode_present, 'Test to disable tftp server '\
                                    'secure mode failed for ' \
                                    '"show running-config" output  -FAILED!'

    step("### Test to delete DHCP dynamic configuration ###")
    range_deleted = True
    sw1('dhcp-server'.format(**locals()))
    sw1('no range test-range start-ip-address 10.0.0.1 '
        'end-ip-address 10.0.0.254 '
        'netmask 255.0.0.0 match tags tag1,tag2,tag3 '
        'set tag test-tag broadcast 10.0.0.255 '
        'lease-duration 60'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "test-range" in line \
            and "10.0.0.1" in line \
            and "10.0.0.254" in line and "255.0.0.0" in line \
            and "tag1,tag2,tag3" in line and "test-tag" in line \
                and "10.0.0.255" in line and "60" in line:
                range_deleted = False

    assert range_deleted, 'Test to delete DHCP Dynamic configuration failed ' \
                          'for "show dhcp-server" output -FAILED!'

    range_deleted = True
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "test-range" in line \
            and "10.0.0.1" in line \
            and "10.0.0.254" in line and "255.0.0.0" in line \
            and "tag1,tag2,tag3" in line and "test-tag" in line \
                and "10.0.0.255" in line and "60" in line:
                range_deleted = False

    assert range_deleted, 'Test to delete DHCP Dynamic configuration failed ' \
                          'for "show running-config" output -FAILED!'

    step("### Test to delete DHCP dynamic ipv6 configuration ###")
    range_created = True
    sw1('no range range-ipv6 '
        'start-ip-address 2001:cdba::3257:9652 '
        'end-ip-address 2001:cdba::3257:9655 '
        'prefix-len 64 '
        'match tags v6tag1,v6tag2,v6tag3 '
        'set tag v6-stag '
        'lease-duration 60'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "range-ipv6" in line \
            and "2001:cdba::3257:9652" in line \
            and "2001:cdba::3257:9655" in line and "64" in line \
            and "v6tag1,v6tag2,v6tag3" in line and "v6-stag" in line \
                and "60" in line:
                range_created = False

    assert range_created, 'Test to delete DHCP Dynamic ipv6 ' \
                          'configuration failed for ' \
                          '"show dhcp-server" output -FAILED!'

    range_created = True
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "range-ipv6" in line \
            and "2001:cdba::3257:9652" in line \
            and "2001:cdba::3257:9655" in line and "64" in line \
            and "v6tag1,v6tag2,v6tag3" in line and "v6-stag" in line \
                and "60" in line:
                range_created = False

    assert range_created, 'Test to delete DHCP Dynamic ipv6 ' \
                          'configuration failed for ' \
                          '"show running-config" output -FAILED!'

    step("### Test to delete DHCP static configuration ###")
    static_created = True
    sw1('no static 192.168.0.2 '
        'match-mac-addresses aa:bb:cc:dd:ee:ff '
        'set tags tag4,tag5,tag6 '
        'match-client-id testid '
        'match-client-hostname testname '
        'lease-duration 60'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "192.168.0.2" in line \
            and "aa:bb:cc:dd:ee:ff" in line \
            and "testid" in line \
            and "tag4,tag5,tag6" in line \
            and "testname" in line \
                and "60" in line:
                static_created = False

    assert static_created, 'Test to delete DHCP static configuration ' \
                           'failed for "show dhcp-server" output -FAILED!'

    static_created = True
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "192.168.0.2" in line \
            and "aa:bb:cc:dd:ee:ff" in line \
            and "testid" in line \
            and "tag4,tag5,tag6" in line \
            and "testname" in line \
                and "60" in line:
                static_created = False

    assert static_created, 'Test to delete DHCP static configuration ' \
                           'failed for "show running-config" output -FAILED!'

    step("### Test to delete DHCP static ipv6 configuration ###")
    static_created = True
    sw1('no static 2001:cdba::3257:9680 '
        'match-mac-addresses ae:bb:cc:dd:ee:ff '
        'set tags v6-stag1,v6-stag2,v6-stag3 '
        'match-client-id v6testid '
        'match-client-hostname v6testname '
        'lease-duration 60'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "2001:cdba::3257:9680" in line \
            and "ae:bb:cc:dd:ee:ff" in line \
            and "v6testid" in line \
            and "v6-stag1,v6-stag2,v6-stag3" in line \
            and "v6testname" in line \
                and "60" in line:
                static_created = False

    assert static_created, 'Test to delete DHCP static ipv6 ' \
                           'configuration failed for ' \
                           '"show dhcp-server" output -FAILED!'

    static_created = True
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "2001:cdba::3257:9680" in line \
            and "ae:bb:cc:dd:ee:ff" in line \
            and "v6testid" in line \
            and "v6-stag1,v6-stag2,v6-stag3" in line \
            and "v6testname" in line \
                and "60" in line:
                static_created = False

    assert static_created, 'Test to delete DHCP static ipv6 ' \
                           'configuration failed for ' \
                           '"show running-config" output -FAILED!'

    step("### Test to delete DHCP Option-name ###")
    option_created = True
    sw1('no option '
        'set option-name opt-name '
        'option-value 192.168.0.1 '
        'match tags mtag1,mtag2,mtag3'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "opt-name" in line \
            and "192.168.0.1" in line \
            and "False" in line \
                and "mtag1,mtag2,mtag3" in line:
                option_created = False

    assert option_created, 'Test to delete DHCP Option-name ' \
                           'failed for "show dhcp-server" ' \
                           'output-FAILED!'

    option_created = True
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "opt-name" in line \
            and "192.168.0.1" in line \
            and "False" in line \
                and "mtag1,mtag2,mtag3" in line:
                option_created = False

    assert option_created, 'Test to delete DHCP Option-name ' \
                           'failed for "show running-config" ' \
                           'output -FAILED!'

    step("### Test to delete DHCP Option-number ###")
    option_created = True
    sw1('no option '
        'set option-number 3 '
        'option-value 192.168.0.3 '
        'match tags mtag4,mtag5,mtag6'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "3" in line \
            and "192.168.0.3" in line \
            and "False" in line \
                and "mtag4,mtag5,mtag6" in line:
                option_created = False

    assert option_created, 'Test to delete DHCP Option-name ' \
                           'with tag matches ' \
                           'failed for "show dhcp-server" ' \
                           'output -FAILED!'

    option_created = True
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "3" in line \
            and "192.168.0.3" in line \
            and "False" in line \
                and "mtag4,mtag5,mtag6" in line:
                option_created = False

    assert option_created, 'Test to delete DHCP Option-name ' \
                           'with tag matches ' \
                           'failed for "show running-config" ' \
                           'output -FAILED!'

    step("### Test to delete DHCP match number ###")
    match_created = True
    sw1('no match '
        'set tag stag '
        'match-option-number 4 '
        'match-option-value 192.168.0.4'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "4" in line \
            and "192.168.0.4" in line \
                and "stag" in line:
                match_created = False

    assert match_created, 'Test to delete DHCP match number ' \
                          'failed for "show dhcp-server" ' \
                          'output -FAILED!'

    match_created = True
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "4" in line \
            and "192.168.0.4" in line \
                and "stag" in line:
                match_created = False

    assert match_created, 'Test to delete DHCP match number ' \
                          'failed for "show running-config" ' \
                          'output -FAILED!'

    step("### Test to delete DHCP match name ###")
    match_created = True
    sw1('no match '
        'set tag temp-mtag '
        'match-option-name temp-mname '
        'match-option-value 192.168.0.5'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "test-mname" in line \
            and "192.168.0.5" in line \
                and "test-mtag" in line:
                match_created = False

    assert match_created, 'Test to delete DHCP match name ' \
                          'failed for "show dhcp-server" ' \
                          'output -FAILED!'

    match_created = True
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "test-mname" in line \
            and "192.168.0.5" in line \
                and "test-mtag" in line:
                match_created = False

    assert match_created, 'Test to delete DHCP match name ' \
                          'failed for "show running-config" ' \
                          'output -FAILED!'

    step("### Test to delete DHCP bootp ###")
    boot_created = True
    sw1('no boot '
        'set file /tmp/testfile '
        'match tag boottag'.format(**locals()))

    dump = sw1('do show dhcp-server'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "/tmp/testfile" in line and "boottag" in line:
            boot_created = False

    assert boot_created, 'Test to delete DHCP bootp ' \
                         'failed for "show dhcp-server" ' \
                         'output -FAILED!'

    boot_created = True
    dump = sw1('do show running-config'.format(**locals()))
    lines = dump.split('\n')
    for line in lines:
        if "/tmp/testfile" in line and "boottag" in line:
            boot_created = False

    assert boot_created, 'Test to delete DHCP bootp ' \
                         'failed for "show running-config" ' \
                         'output -FAILED!'
