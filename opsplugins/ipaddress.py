#!/usr/bin/env python
# Copyright (C) 2015-2016 Hewlett Packard Enterprise Development LP
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

import socket
import struct


def is_valid_ip_address(ip):
    is_ipv4 = True
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            is_ipv4 = False
        except:
            return False

    if is_ipv4 and not is_valid_ipv4(ip2int(ip)):
        return False

    if not is_ipv4 and not is_ipv6_global_unicast(ipv6_to_int(ip)):
        return False
    return True


def ip2int(ip):
    return struct.unpack("!I", socket.inet_pton(socket.AF_INET, ip))[0]


def ipv6_to_int(ip):
    tup1, tup2 = struct.unpack("!QQ", socket.inet_pton(socket.AF_INET6, ip))
    return (tup1 << 64) | tup2


def is_valid_ipv4(ip):
    return not (is_broadcast_ipv4(ip) or is_loopback_ipv4(ip) or
                is_multicast_ipv4(ip) or is_experimental_ipv4(ip) or
                is_invalid_ipv4(ip) or is_subnet_broadcast(ip) or
                is_network_address(ip))


def is_broadcast_ipv4(ip):
    return ((ip & 0xffffffff) == 0xffffffff)


def is_loopback_ipv4(ip):
    return ((ip & 0x7f000000) == 0x7f000000)


def is_multicast_ipv4(ip):
    return ((ip & 0xf0000000) == 0xe0000000)


def is_experimental_ipv4(ip):
    return ((ip & 0xf0000000) == 0xf0000000)


def is_invalid_ipv4(ip):
    return (ip == 0)


def is_subnet_broadcast(ip):
    return ((ip & 0x000000ff) == 0xff)


def is_network_address(ip):
    return ((ip & 0x000000ff) == 0x0)


def is_ipv6_global_unicast(ip):
    return not (in6_is_addr_unspecified(ip) or in6_is_addr_loopback(ip) or
                in6_is_addr_sitelocal(ip) or in6_is_addr_multicast(ip) or
                in6_is_addr_linklocal(ip))


def in6_is_addr_unspecified(ip):
    return (ip == 0)


def in6_is_addr_loopback(ip):
    return (ip == 1)


def in6_is_addr_sitelocal(ip):
    return ((ip & 0xfec00000000000000000000000000000) ==
            0xfec00000000000000000000000000000)


def in6_is_addr_multicast(ip):
    return ((ip & 0xff000000000000000000000000000000) ==
            0xff000000000000000000000000000000)


def in6_is_addr_linklocal(ip):
    return ((ip & 0xfec00000000000000000000000000000) ==
            0xfe800000000000000000000000000000)
