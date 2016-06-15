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
from os.path import isabs
from os.path import isdir

class DhcpTftpServerValidator(BaseValidator):
    resource = "system"

    def validate_modification(self, validation_args):
        system_row = validation_args.resource_row
        if hasattr(system_row, "other_config"):
            other_config = get_column_data_from_row(system_row, "other_config")
            tftp_server_path_value = other_config.get("tftp_server_path", None)
            if not self.is_valid_tftp_server_path(tftp_server_path_value):
                details = "The directory %s does not exist. " \
                          "Please configure a valid absolute path." \
                           % (tftp_server_path_value)
                raise ValidationError(error.VERIFICATION_FAILED, details)


    def is_valid_tftp_server_path(self, path):
        if (path is not None) and \
           isabs(path) and isdir(path):
            return True
        else:
            return False
