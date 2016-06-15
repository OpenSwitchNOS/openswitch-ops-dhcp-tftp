#!/usr/bin/env python
# Copyright (C) 2016 Hewlett Packard Enterprise Development LP
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import macaddress

MAX_DHCP_CONFIG_NAME_LENGTH = 15


def is_valid_tags(match_tags):
    for tag in match_tags:
        if len(tag) > MAX_DHCP_CONFIG_NAME_LENGTH:
            return False
    return True


def is_valid_tag(tag):
    if len(tag) > MAX_DHCP_CONFIG_NAME_LENGTH:
        return False
    else:
        return True


def is_valid_option_number(num):
    if (num >= 255):
        return False
    else:
        return True


def is_valid_lease_duration(lease_duration):
    if (lease_duration == 1) or (lease_duration > 65535):
        return False
    else:
        return True


def is_valid_mac_addresses(mac_addresses):
    for mac_address in mac_addresses:
        if not macaddress.is_valid_mac_address(mac_address):
            return False
    return True
