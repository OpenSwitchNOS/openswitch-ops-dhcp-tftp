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
import ipaddress


class DHCPSrvRangeValidator(BaseValidator):
    resource = "dhcpsrv_range"

    def validate_modification(self, validation_args):
        lease_duration = None
        end_ip_address = None
        DHCPSrv_Range_row = validation_args.resource_row
        start_ip_address = get_column_data_from_row(DHCPSrv_Range_row,
                                                    "start_ip_address")

        if hasattr(DHCPSrv_Range_row, "end_ip_address"):
            end_ip_address = get_column_data_from_row(DHCPSrv_Range_row,
                                                      "end_ip_address")
        if hasattr(DHCPSrv_Range_row, "lease_duration"):
            lease_duration = get_column_data_from_row(DHCPSrv_Range_row,
                                                      "lease_duration")
        if not ipaddress.is_valid_ip_address(start_ip_address):
            details = "%s is invalid." % (start_ip_address)
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if (end_ip_address is not None) and \
           (not ipaddress.is_valid_ip_address(end_ip_address)):
            details = "%s is invalid." % (end_ip_address)
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if (lease_duration is not None) and \
           (not self.is_valid_lease_duration(lease_duration)):
            details = "Lease duration should be 0 for infinite or between " \
                      "2-65535."
            raise ValidationError(error.VERIFICATION_FAILED, details)

    def is_valid_lease_duration(self, lease_duration):
        if (lease_duration == 1) or (lease_duration > 65535):
            return False
        else:
            return True
