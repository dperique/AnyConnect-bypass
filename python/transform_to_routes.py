#!/usr/bin/env python3

"""
Get the statfile like this: /opt/cisco/anyconnect/bin/vpn stats > mystatFile.txt

The format of the stat file looks like:

[ Secured Routes (IPv4) ]

    Network                                Subnet             Host(s)
    x.x.x.x                                28
    x.x.x.x                                28
    x.x.x.x                                28

[ Secured Routes (IPv6) ]

    Network                                Subnet             Host(s)
    ...

This will parse the file from the output of /opt/cisco/anyconnect/bin/vpn stats
and transform it into a set of static "route add" commands that can be run. We
support linux and macOS.

This tool help if you want to implement an AnyConnect bypass.

./transform_to_routes.py mystatFile.txt 192.168.1.231 macOS ;# dump route commands for macOS
./transform_to_routes.py mystatFile.txt 192.168.1.231 linux ;# dump route commands for linux
"""

import sys
import re
from typing import List, Tuple

def transform_to_routes(aStatFile: str, aGw: str, aMode: str) -> Tuple[int, List]:

    """
    Return a return code (0 = success) and list of strings that represent
    the route commands for the given mode in aMode.
    Return code will be 1 if error and the list of strings will container the error.
    """
    retCode = 0
    retList = []

    with open(aStatFile) as f:

        # Read upto the "Secured Routes (IPv4)".
        #
        while f:
            line = f.readline()
            if "Secured Routes (IPv4)" in line:

                # Consume two more lines
                f.readline()
                f.readline()
                break
        else:
            retList.append("Error looking for the secured ipv4 routes")
            retCode = 1

        while f:
            line = f.readline()
            if "Secured Routes (IPv6)" in line:
                break

            if len(line) < 3:
                # Deal with blank line with maybe a space or two
                continue

            split_line = line.split()
            route = split_line[0]
            netmask= split_line[1]
            if aMode == "linux":
                if netmask == "32":
                    retList.append(f"route add -host {route} gw {aGw}")
                else:
                    retList.append(f"route add -net {route}/{netmask} gw {aGw}")
            elif aMode == "macOS":
                retList.append(f"sudo route -n add {route}/{netmask} {aGw}")
            else:
                retList.append(f"Uncaught value for 'aMode':{aMode}")
                retCode = 1
                break
        else:
            print("Error finding end of secured ipv4 routes")
            retCode = 1

    return (retCode, retList)

if __name__ == "__main__":

    if len(sys.argv) < 4:
      print(f"Usage: {sys.argv[0]} aStatFile aGw aMode")
      print()
      print("  aStatfile: get this via /opt/cisco/anyconnect/bin/vpn stats > mystatFile.txt")
      print("  aGw: the IP address of the device running AnyConnect with access to target networks")
      print("  aMode: linux or macOS")
      print()
      sys.exit(0)

    # The file will be validated during the parse.
    aStatFile = sys.argv[1]

    # Validate the Gateway IPv4 address.
    aGw = sys.argv[2]
    if not re.search("^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$", aGw):
        print(f"'{aGw}' is not a valid IPv4 address")
        sys.exit(0)

    # Validate the mode (we only support two modes).
    aMode = sys.argv[3]
    mode_list = ["linux", "macOS"]
    if aMode not in mode_list:
        print(f"Unknown Mode; please chose one of: {mode_list}")
        sys.exit(0)

    retTup = transform_to_routes(aStatFile, aGw, aMode)
    if retTup[0] == 0:
        # Successful run -- print out the routes
        #
        for line in retTup[1]:
            print(line)
