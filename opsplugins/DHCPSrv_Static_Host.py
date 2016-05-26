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
