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


class DHCPSrvStaticHostValidator(BaseValidator):
    resource = "dhcpsrv_static_host"

    def validate_modification(self, validation_args):
        mac_addresses = None
        set_tags = None
        client_id = None
        client_hostname = None
        lease_duration = None

        DHCPSrv_Static_Host = validation_args.resource_row
        ip_address = get_column_data_from_row(DHCPSrv_Static_Host,
                                              "ip_address")

        if not ipaddress.is_valid_ip_address(ip_address):
            details = "%s is an invalid IP address." % (ip_address)
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Static_Host, "mac_addresses"):
            mac_addresses = get_column_data_from_row(DHCPSrv_Static_Host,
                                                     "mac_addresses")
        if (mac_addresses is not None) and \
           (not dhcptftpservervalidations.is_valid_mac_addresses(
                mac_addresses)):
            details = "Invalid MAC addresses."
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Static_Host, "set_tags"):
            set_tags = get_column_data_from_row(DHCPSrv_Static_Host,
                                                "set_tags")

        if (set_tags is not None) and \
           (not dhcptftpservervalidations.is_valid_tags(set_tags)):
            details = "%s is invalid." % (set_tags)
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Static_Host, "client_hostname"):
            client_hostname = get_column_data_from_row(DHCPSrv_Static_Host,
                                                       "client_hostname")

        if (client_hostname is not None):
            for hostname in client_hostname:
                if (len(hostname) > MAX_DHCP_CONFIG_NAME_LENGTH):
                    details = "%s is invalid." % (hostname)
                    raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Static_Host, "client_id"):
            client_id = get_column_data_from_row(DHCPSrv_Static_Host,
                                                 "client_id")

        if (client_id is not None):
            for id in client_id:
                if (len(id) > MAX_DHCP_CONFIG_NAME_LENGTH):
                    details = "%s is invalid." % (id)
                    raise ValidationError(error.VERIFICATION_FAILED, details)

        if (mac_addresses is None) and (client_hostname is None) and \
           (client_id is None):
            details = "Any one of MAC address or hostname or client-id" \
                      " must be specified"
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Static_Host, "lease_duration"):
            lease_duration = get_column_data_from_row(DHCPSrv_Static_Host,
                                                      "lease_duration")

        if (lease_duration is not None):
            for duration in lease_duration:
                if (not dhcptftpservervalidations.is_valid_lease_duration(
                        duration)):
                    details = "Lease duration should be 0 for infinite or" \
                              " between 2-65535."
                    raise ValidationError(error.VERIFICATION_FAILED, details)
