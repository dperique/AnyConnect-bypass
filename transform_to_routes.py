#!/usr/bin/env python3

"""
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
"""

import sys

if len(sys.argv) < 4:
  print(f"Usage: {sys.argv[0]} aStatFile aGw aMode")
  print()
  print("  aStatfile: get this via /opt/cisco/anyconnect/bin/vpn stats > mystatFile.txt")
  print("  aGw: the IP address of the device running AnyConnect with access to target networks")
  print("  aMode: linux or macOS")
  sys.exit(0)

aStatFile = sys.argv[1]
aGw = sys.argv[2]
aMode = sys.argv[3]
if aMode not in ["linux", "macOS"]:
    print("Unknown Mode")
    sys.exit(0)

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
        print("Error looking for the secured ipv4 routes")
        sys.exit(0)

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
                print(f"route add -host {route} gw {aGw}")
            else:
                print(f"route add -net {route}/{netmask} gw {aGw}")
        elif aMode == "macOS":
            print(f"sudo route -n add {route}/{netmask} {aGw}")
        else:
            print(f"Uncaught value for 'aMode':{aMode}")
    else:
        print("Error finding end of secured ipv4 routes")
        sys.exit(0)
