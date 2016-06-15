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


class DHCPSrvOptionValidator(BaseValidator):
    resource = "dhcpsrv_option"

    def validate_modification(self, validation_args):
        option_name = None
        option_number = None
        match_tags = None
        DHCPSrv_Option_row = validation_args.resource_row

        if hasattr(DHCPSrv_Option_row, "option_name"):
            option_name = get_column_data_from_row(DHCPSrv_Option_row,
                                                   "option_name")
        if (option_name is not None):
            for name in option_name:
                if (not dhcptftpservervalidations.is_valid_tag(name)):
                    details = "%s is invalid." % (name)
                    raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Option_row, "match_tags"):
            match_tags = get_column_data_from_row(DHCPSrv_Option_row,
                                                  "match_tags")
        if (match_tags is not None) and \
           (not dhcptftpservervalidations.is_valid_tags(match_tags)):
            details = "%s is invalid." % (match_tags)
            raise ValidationError(error.VERIFICATION_FAILED, details)

        if hasattr(DHCPSrv_Option_row, "option_number"):
            option_number = get_column_data_from_row(DHCPSrv_Option_row,
                                                     "option_number")
        if (option_number is not None):
            for number in option_number:
                if (not dhcptftpservervalidations.is_valid_option_number(
                        number)):
                    details = "%s is invalid." % (number)
                    raise ValidationError(error.VERIFICATION_FAILED, details)
