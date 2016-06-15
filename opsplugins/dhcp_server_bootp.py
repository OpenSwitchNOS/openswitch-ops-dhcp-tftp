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
from opsrest.utils import *
import dhcptftpservervalidations


class DhcpTftpServerBootpValidator(BaseValidator):
    resource = "dhcp_server"

    def validate_modification(self, validation_args):
        dhcp_server_row = validation_args.resource_row
        if hasattr(dhcp_server_row, "bootp"):
            bootp = get_column_data_from_row(dhcp_server_row, "bootp")
            tag_value = bootp.get("match tag", None)
            if (tag_value is not None) and \
               (not dhcptftpservervalidations.is_valid_tag(tag_value)):
                details = "%s is invalid." % (tag_value)
                raise ValidationError(error.VERIFICATION_FAILED, details)
