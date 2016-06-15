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

from opsvalidator.base import BaseValidator
from opsvalidator import error
from opsvalidator.error import ValidationError
from opsrest.utils.utils import get_column_data_from_row
import dhcptftpservervalidations
import ipaddress


MAX_DHCP_CONFIG_NAME_LENGTH = 15


class DHCPSrvRangeValidator(BaseValidator):
    resource = "dhcpsrv_range"

    def validate_modification(self, validation_args):
        lease_duration = None
        start_ip_address = None
        end_ip_address = None
        name = None
        set_tag = None
        match_tags = None
        netmask = None
        broadcast = None
        prefix_len = None
        net_mask = None
        end_ip = None
        broad_cast = None
        prefixlen = None

        DHCPSrv_Range_row = validation_args.resource_row
        name = get_column_data_from_row(DHCPSrv_Range_row,
                                        "name")
        if len(name) > MAX_DHCP_CONFIG_NAME_LENGTH:
            details = "%s is invalid." % (name)
            raise ValidationError(error.VERIFICATION_FAILED, details)

        start_ip_address = get_column_data_from_row(DHCPSrv_Range_row,
                                                    "start_ip_address")

        if not ipaddress.is_valid_ip_address(start_ip_address):
            details = "%s is invalid." % (start_ip_address)
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Range_row, "end_ip_address"):
            end_ip_address = get_column_data_from_row(DHCPSrv_Range_row,
                                                      "end_ip_address")

        if (end_ip_address is not None):
            for ip in end_ip_address:
                end_ip = ip
                if (not ipaddress.is_valid_ip_address(ip)):
                    details = "%s is invalid." % (ip)
                    raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Range_row, "lease_duration"):
            lease_duration = get_column_data_from_row(DHCPSrv_Range_row,
                                                      "lease_duration")

        if (lease_duration is not None):
            for duration in lease_duration:
                if (not dhcptftpservervalidations.is_valid_lease_duration
                   (duration)):
                    details = "Lease duration should be 0 for infinite or " \
                              "between 2-65535."
                    raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Range_row, "name"):
            name = get_column_data_from_row(DHCPSrv_Range_row,
                                            "name")

        if (start_ip_address is not None) and \
           (end_ip is not None) and \
           (ipaddress.ip_type(start_ip_address) != ipaddress.ip_type(end_ip)):
            details = "Invalid IP address range"
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Range_row, "set_tag"):
            set_tag = get_column_data_from_row(DHCPSrv_Range_row,
                                               "set_tag")

        if (set_tag is not None):
            for tag in set_tag:
                if (len(tag) > MAX_DHCP_CONFIG_NAME_LENGTH):
                    details = "%s is invalid." % (tag)
                    raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Range_row, "match_tags"):
            match_tags = get_column_data_from_row(DHCPSrv_Range_row,
                                                  "match_tags")

        if (match_tags is not None) and \
           (not dhcptftpservervalidations.is_valid_tags(match_tags)):
            details = "%s is invalid." % (match_tags)
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Range_row, "netmask"):
            netmask = get_column_data_from_row(DHCPSrv_Range_row,
                                               "netmask")

        if (netmask is not None):
            for mask in netmask:
                net_mask = mask
                if (not ipaddress.is_valid_netmask(mask)):
                    details = "%s is invalid." % (mask)
                    raise ValidationError(error.VERIFICATION_FAILED, details)

        if (start_ip_address is not None) and \
           (end_ip is not None) and \
           (net_mask is not None) and \
           (ipaddress.ip_type(start_ip_address) == 0) and \
           (not ipaddress.is_valid_net(start_ip_address, end_ip, net_mask)):
            details = "Invalid IP address range."
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if (start_ip_address is not None) and \
           (ipaddress.ip_type(start_ip_address) == 1) and \
           (net_mask is not None):
            details = "Error : netmask configuration not allowed for IPv6"
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Range_row, "broadcast"):
            broadcast = get_column_data_from_row(DHCPSrv_Range_row,
                                                 "broadcast")

        if broadcast is not None:
            for b in broadcast:
                broad_cast = b

        if (start_ip_address is not None) and \
           (ipaddress.ip_type(start_ip_address) == 0) and \
           (net_mask is not None) and \
           (broad_cast is not None) and \
           (not ipaddress.is_valid_broadcast_addr(start_ip_address,
                                                  net_mask,
                                                  broad_cast)):
            details = "%s is invalid." % (broad_cast)
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if (start_ip_address is not None) and \
           (broad_cast is not None) and \
           (net_mask is None):
            details = "Error : netmask must be specified before broadcast " \
                      "address"
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if (start_ip_address is not None) and \
           (net_mask is not None) and \
           (broad_cast is not None) and \
           (ipaddress.ip_type(start_ip_address) == 1):
            details = "Error : broadcast address not allowed for IPv6"
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Range_row, "prefix_len"):
            prefix_len = get_column_data_from_row(DHCPSrv_Range_row,
                                                  "prefix_len")

        if prefix_len is not None:
            for p in prefix_len:
                prefixlen = p

        if (start_ip_address is not None) and \
           (end_ip is not None) and \
           (prefixlen is not None) and \
           (ipaddress.ip_type(start_ip_address) != 1):
            details = "Error: prefix length configuration not allowed for IPv4"
            raise ValidationError(error.VERIFICATION_FAILED, details)
