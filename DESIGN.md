#DHCP-TFTP server component design

##Contents
   - [High level design of DHCP-TFTP](#high-level-design-of-dhcp-tftp)
   - [Design choices](#design-choices)
   - [Participating modules](#participating-modules)
       - [OVSDB-Schema](#ovsdb-schema)
           - [DHCP server column in VRF table](#dhcp-server-column-in-vrf-table)
           - [DHCP server table](#dhcp-server-table)
           - [DHCP server range table](#dhcp-server-range-table)
           - [DHCP server static host table](#dhcp-server-static-host-table)
           - [DHCP server option table](#dhcp-server-option-table)
           - [DHCP server match table](#dhcp-server-match-table)
           - [Other config column in System table](#other-config-column-in-system-table)
       - [DHCP Leases DB](#dhcp-leases-db)

##High level design of DHCP-TFTP

The DHCP-TFTP feature provides the DHCP server and TFTP server functionality. OpenSwitch uses open source `Dnsmasq` for DHCP server and TFTP server functionality. The configuration specific to DHCP server and TFTP server are maintained in OVSDB. The user configuration of DHCP and TFTP server are updated in OVSDB through CLI and REST daemons. The DHCP-TFTP python daemon reads the DHCP-TFTP server configuration from OVSDB and starts the DHCP-TFTP server daemon (dnsmasq) by streaming in the configuration as CLI options to the binary. The DHCP-TFTP python daemon also monitors the OVSDB for any configuration changes specific to DHCP-TFTP server and if there are any configuration changes, the DHCP-TFTP python daemon restarts the server daemon (dnsmasq) with the new configuration.

The DHCP leases information is maintained separately in a persistent DHCP leases database. Whenever the DHCP-TFTP server daemon (dnsmasq) assigns a new IP address to clients or the leases information pertaining to already-assigned IP address changes or expires, it invokes a DHCP leases script that passes the leases information as arguments to the script. The DHCP leases script would update this leases information in the DHCP leases database. During the init time of DHCP-TFTP server (dnsmasq), it invokes the same DHCP leases script with **init** argument and the DHCP leases script reads the leases information from the DHCP leases database and sends it to the DHCP-TFTP server daemon. For displaying the DHCP server leases information to the user, the CLI and REST daemons invoke the same DHCP leases script with **show** argument and the DHCP leases script reads the leases information from the leases database and sends it to the CLI and REST daemons.

##Design choices

There are multiple open source choices available for the DHCP-TFTP server. The open source `Dnmasq` was chosen based on the following considerations:

* It is a very common, simple implementation of the DHCP server and TFTP server.
* It is being heavily used already where small, occasional use of the DHCP server and TFTP server are needed.
* For distributing IPs and providing PXE images to the servers in rack, this is one of the most suitable options.

##Participating modules

```

                     +------------------------------------+
                     |                                    |
                     |            CLI and REST            |
                     |                                    |
                     +----+-------------------------+-----+
                          |                         |
                          |                         |
                          |                         |
    +---------------------+---+                +----+---------------------+
    |                         |                |                          |
    |       OVSDB             |                | DHCP leases python script|
    |                         |                |                          |
    +----------+--------------+                +----+----------------+----+
               |                                    |                |
               |                                    |                |
               |                                    |                |
    +----------+--------------+                     |      +---------+---------+
    |                         |                     |      |                   |
    | DHCP-TFTP python daemon |                     |      |  DHCP Leases DB   |
    |                         |                     |      |                   |
    +---------------------+---+                     |      +-------------------+
                          |                         |
                          |                         |
                          |                         |
                    +-----+-------------------------+-----+
                    |                                     |
                    |           DHCP-TFTP server          |
                    |                                     |
                    +-------------------------------------+

```

###OVSDB-Schema
The OVSDB is the central database used in OpenSwitch. All the communication between different modules are facilitated through this database. The following tables and columns are used in the OVSDB for DHCP-TFTP server functionality:

* DHCP server column in VRF table
* DHCP server table
* DHCP server range table
* DHCP server static host table
* DHCP server option table
* DHCP server match table
* Other config column in System table (for TFTP server configuration)

####DHCP server column in VRF table
To facilitate each VRF having a separate DHCP server instance, the VRF table has a direct reference to the DHCP server table.

####DHCP server table
The DHCP server table has the following columns:

- **Ranges**: This column has a direct reference to the DHCP server range table.

- **Static hosts**: This column has a direct reference to the DHCP server static host table.

- **DHCP options**: This column has a direct reference to the DHCP server option table.

- **Matches**: This column has a direct reference to the DHCP server match table.

- **Bootp**: This column has key=value pairs mapping of BOOTP options for the network boot of DHCP clients. The key is the configured matching tag and value is the TFTP boot file configured for the matching tag.

####DHCP server range table
The DHCP server range table stores the dynamic IP address ranges configuration of the DHCP server and has the following columns:

```
Name
Start IP address
End IP address
Netmask
Broadcast
Prefix length
Constructor
Set tag
Match tags
Static
Lease duration
```

####DHCP server static host table
The DHCP server static host table stores the static leases configured by the user and has the following columns:

```
IP address
MAC addresses
Client hostname
Client ID
Set tags
Lease duration
```

####DHCP server option table
The DHCP server option table stores the user configuration to specify DHCP options that would be sent to the DHCP clients and has the following columns:

```
Option name
Option number
Option value
Match tags
IPv6
```

####DHCP server match table
The DHCP server match table stores the user configuration to set tags for the incoming DHCP requests based on the options and its value sent by the clients and has the following columns:

```
Option name
Option number
Option value
Set tag
```

####Other config column in System table
The following key=value pair mappings are used in other config column of system table for TFTP server configuration:

* The key **tftp_server_enable** would have the value **true** if TFTP server is enabled and **false** if TFTP server is disabled.
* The key **tftp_server_secure** would have the value **true** if TFTP server secure mode is enabled and **false** if TFTP server secure mode is disabled.
* The key **tftp_server_path** would have the value of absolute path of the TFTP root directory if configured by the user.

### DHCP Leases DB
The DHCP leases database is a separate persistent database to store the DHCP leases information. It has the DHCP lease table with the following columns:

```
Expiry time
MAC address
IP address
Client hostname
Client ID
```
