## Introduction

The idea is to get packets from machine A (the one wanting access to
the target network) to machine B (the one giving access to the other
network -- the bypass router).

The methods in the main README.md mention using plain routing.  This
doc, mentions two other ways:

* via GRE tunnel
* via VPN (using openvpn)

# How to

get VM with two interfaces: one with NAT'ed and one with bridged

For WIFI people: this won't work because some wifi drivers don't support
promiscuous and so the host IP will respond to ARP (instead of the IP on
the bridged interface) and so packets cannot come to the bridged
interface and so they cannot be SNAT'ed or forwarded.

For Wired people: this will work -- just point your routes to the
bridged IP.

The sample configuration in my home lab:

One machine "vicky-wifi" (MacOS) running AnyConnect with access to
"target" networks.

Two client machines that want access to the AnyConnect networks:

* mozart (MacOS) 192.168.1.105
* bionics (Ubuntu 18.04) 192.168.1.118

The "bypassRouter" (an Unbuntu 18.04 VM) running on the machine
running AnyConnect.  Set the first interface as NAT'ed and the second
interface as Bridged (192.168.1.244).

The two client machines have target routes configured with the gateway
set to one of:

* For bypassRouter in "wired" mode, the gateway is set to the IP address
  of the bypassRouter's Bridged interface (192.168.1.244)
* For bypassRouter in "tunnel" mode, the gateway is set to the IP address
  of the tunnel configured on the bypassRouter

To get things going, do this:

First setup a tunnel from your client machine to the bypassRouter.
The idea is to make a tunnel so that packets can be transported from
your client machines to the bypassRouter where they can be SNAT'ed and
forwarded.  Because the packets are inside the tunnel, the limitation
mentioned above for WIFI no longer applies.

To setup the tunnel, use of these methods:

* bypassRouter in GRE tunnel mode:

```
# Run this on the bypassRouter where <anIP> is the IP address of
# a client machine and <bypassIP> is the IP address of the bypassRouter's
# Bridged interface.
#
# NOTE: ensure that the 10.0.0.1 and 10.0.0.2 subnets are unused.
#
sudo ip tunnel add gre1 mode gre local <bypassIP> remote <anIP> ttl 255
sudo ip addr add 10.0.0.1/30 dev gre1
sudo ip link set gre1 up

# Run this on the client machine with IP address of <anIP>.
#
sudo ip tunnel add gre1 mode gre local <anIP> remote <bypassIP> ttl 255
sudo ip addr add 10.0.0.2/30 dev gre1
sudo ip link set gre1 up
```

* bypassRouter in vpn tunnel mode:

Here are a few helpful links:

* [nice link I used for the example](https://www.cs.put.poznan.pl/csobaniec/examples/openvpn/).
* [openvpn doc](https://openvpn.net/community-resources/how-to/#scope)

We use OpenVPN with a configuration like this:

Create this file which will be the OpenVPN server configuration file.
Ensure the 11.0.0.1 and 11.0.0.2 networks are unused on the bypassRouter.

bypassVpnServer.conf:

```
dev tun
ifconfig 11.0.0.1 11.0.0.2
secret bypassVpnServer.key
```

bypassVpnServer.key is the vpn password.  Generate one like this:

```
openvpn --genkey --secret bypassVpnServer.key
```

Install and startup openvpn:

```
apt-get -y install openvpn
openvpn bypassVpnServer.conf &
```

Verify that the vpn is up and listening on port 1194:

```
$ sudo netstat -nap|grep 1194
udp        0      0 0.0.0.0:1194       0.0.0.0:    26249/openvpn
```

If you don't see something like the above, you vpn is not working and
you will need to debug/troubleshoot it.

On the client machine, create a client VPN file called something like
`bypassVpn.conf`:

```
remote <bypassIP>
dev tun
ifconfig 11.0.0.2 11.0.0.1
secret bypassVpnServer.key
```

Get a copy of the bypassVpnServer.key file and place both the
`bypassVpn.conf` and `bypassVpnServer.key` files in the same folder on
your Mac.

On your Mac, install Tunnelblick and double click the `bypassVpn.conf`
file in the Finder so it will add the VPN configuration.  Start the VPN.


## An even better way: use openvpn to install routes

Setup an openvpn server that contains a CA, serverKey/Cert and then have it
add the routes automatically to the client.  This replaces the need to write
a script that can install the routes.

Then create openvpn clients that will login so they get the routes installed
automatically.

See https://github.com/dperique/asus-rt-n66r-openvpn for instructions on how
to create the certs via openssl.

The big advantage of this method is that the client can be any machine that
supports openvpn (iPhones, Android Phones, iPads, Windows machines, etc.)
