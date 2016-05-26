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

from opsvalidator.base import *
from opsvalidator import error
from opsvalidator.error import ValidationError
from opsrest.utils import *
import ipaddress


class DHCPSrvStaticHostValidator(BaseValidator):
    resource = "dhcpsrv_static_host"

    def validate_modification(self, validation_args):
        mac_address = None
        DHCPSrv_Static_Host = validation_args.resource_row
        ip_address = utils.get_column_data_from_row(DHCPSrv_Range_row,
                                                    "ip_address")
        if hasattr(DHCPSrv_Range_row, "mac_address"):
            mac_address = utils.get_column_data_from_row(DHCPSrv_Range_row,
                                                         "mac_addresses")
        if not ipaddress.is_valid_ip_address(ip_address):
            details = "%s is an invalid IP address." % (ip_address)
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if (macaddress is not None) and \
           (not macaddress.is_valid_mac_address(mac_address)):
            details = "%s is an invalid MAC address." % (mac_address)
            raise ValidationError(error.VERIFICATION_FAILED, details)
