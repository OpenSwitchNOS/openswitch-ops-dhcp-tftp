OPS-DHCP-TFTP
=============

What is ops-dhcp-tftp?
----------------------
ops-dhcp-tftp in [OpenSwitch](http://www.openswitch.net), is a python module that is responsible for reading DHCP-TFTP server configuration from OVSDB and starting the DHCP-TFTP server daemon (open source Dnsmasq) by streaming the configuration as command line options to the binary. Also, it monitors the OVSDB for any configuration changes specific to DHCP-TFTP and if there are any configuration changes, then it restarts the DHCP-TFTP server daemon (Dnsmasq) with new configuration.

What is the structure of the repository?
----------------------------------------
* ops-dhcp-tftp python source files are under this subdirectory.
* ./tests/ - contain all the component tests of ops-dhcp-tftp based on ops mininet framework.

What is the license?
--------------------
Apache 2.0 license. For more details refer to [COPYING](https://git.openswitch.net/cgit/openswitch/ops-openvswitch/tree/COPYING)

What other documents are available?
----------------------------------
For the high level design of ops-dhcp-tftp, refer to [DESIGN.md](DESIGN.md)
For general information about OpenSwitch project refer to http://www.openswitch.net
