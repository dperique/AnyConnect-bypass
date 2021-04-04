# Accessing AnyConnect networks without running AnyConnect (bypass it)

Just a test
AnyConnect is used as VPN software so that you can get onto certain network(s), encrypt traffic,
etc.  It serves this purpose well.  However, in order to use AnyConnect, you need certain
certificates and other administrative permissions.  To obtain these, you have to sometimes "give
up" your laptop to some administrative "entity".  If you already run AnyConnect, you were already
issued a laptop owned by that "entity".

These instructions show you how to share access to the network(s) that AnyConnect gives using
your hosts that you do not want to "give up".

# Basic Idea

We take advantage of the fact that AnyConnect exposes (through their CLI) the specific routes
that it encrypts.  I refer to these routes as "target network(s)".

Knowing exactly what routes are needed allows us to configure hosts to use a certain gateway for
these routes.

We can create a gateway that can route traffic to the target network(s) on the host running
AnyConnect (I call this the "AnyConnect host").

This is possible because when a host runs VPN software, that VPN is accessible to VMs running
on that host when those VMs have an interface set in "NAT" mode.  To route traffic to the VPN
networks from an aribitrary host, we use SNAT so that the traffic looks like it came from the
VM.

We run a VM (I refer to it as the "VM gateway") on the AnyConnect host to
act as a router.  We set one of the interfaces of
the VM gateway as the ingress interface
for other devices wanting to get onto the target network(s)
and another interface as NAT.
The idea is that the VM gateway will route packets from hosts using it as a routing gateway
and SNAT the packets through the AnyConnect host and onto the target networks(s).

# Requirements

You will need:
* a host that runs AnyConnect to connect to your target network(s); if you already run
  AnyConnect, you already have this
* that host must be able to run a VM with two interfaces (you can use VMware or VirtualBox)
  * an interface set to NAT
  * an interface set to bridge mode
    * this interface must be pingable from hosts wanting to reach the target network(s)
* You will need a Linux VM (I use Ubuntu 16.04) with root access so that you can install
  NAT rules, and turn on routing.  Also, turn off any powersaving and use static IP addressing
  to avoid hiccups in connectivity during machine sleeping, DHCP lease renews, etc.

  Other VM "routing" appliances will work as long as you can configure SNAT rules on them.

* Hosts that want to get onto the target network(s) need to be able to be configured to
  use the VM gateway as a routing gateway for the routes that AnyConnect is routing.  You
  will need sudo access to install routes.

# Steps

## Run AnyConnect

Ensure you have connectivity to your target network(s).

## Create and start the VM gateway
  * Ensure that you have two interfaces
    * One for NAT.  Take note of the IP address on the VM.  You will use this as the SNAT address.
    * One for ingress for your hosts (this will most likely be bridged onto an Ethernet
      interface where your other hosts (those that don't run AnyConnect) can reach this VM.
      Take note of the IP address.  You will need to use this as the gateway for your other
      hosts.
  * Ensure the VM gateway is setup so that its default gateway is set to the NAT'ing interface
  * For your sanity, set a DNS entry in /etc/resolv.conf on the VM.  This will allow you to ping hosts
    on the target network using DNS names.  This is a nice debugging tool because you don't have
    to deal with IP addresses. You can get DNS addresses from the Network Administrator for
    your target network(s).  You will use these DNS addresses on your other hosts that want to
    reach the target network(s).
  * On the VM gateway ensure you can ping hosts on the target network (e.g., using a DNS name)
  * Determine the NAT'ing interface inside the VM gateway and note its IP address.
  * Turn on forwarding via ``echo 1 >> /proc/sys/net/ipv4/ip_forward`` for Linux or use the
    appropriate command for your gateway VM.

## Determine your SNAT'ing IP address on the VM gateway

  Find the IP address of the interface that leads to the target network(s).  This will be the
  IP address of the interface that is NAT'ing on the VM gateway.

  Here's a way to find it by taking the IP address of a host on the target network(s) and running
  ``ip route get <aHost>``.

  You will see an interface.  Once you have that interface, run ``ifconfig`` on that interface to determine
  it's IP address.  For example:

```
  $ ping myhost   <-- myhost is a host on the target networks(s)
  PING myhost (192.31.5.7) 56(84) bytes of data.
  64 bytes from 192.31.5.7: icmp_seq=1 ttl=63 time=106 ms
  ^C
  --- myhost ping statistics ---
  1 packets transmitted, 1 received, 0% packet loss, time 0ms
  rtt min/avg/max/mdev = 106.631/106.631/106.631/0.000 ms

  $ ip route get 192.31.5.7
  192.31.5.7 via 10.0.2.2 dev enp0s3  src 10.0.2.15    <-- the interface is enp0s3
      cache
  dperiquet@spooner2:~$ ifconfig enp0s3
  enp0s3    Link encap:Ethernet  HWaddr 08:00:27:9d:21:fc
            inet addr:10.0.2.15  Bcast:10.0.2.255  Mask:255.255.255.0  <-- IP address is 10.0.2.15
```
## Add SNAT rule for hosts needing access to target network(s)

  In my case, the IP address on my VM gateway that leads to the target network is 10.0.2.15.
  You will need to use the IP address specific to your VM.
  A host I will use that wants access to the target network(s) is 192.168.1.1.21.

  Run this command so that we forward traffic from 192.168.1.21 as SNAT'ed with source IP address
  of 10.0.2.15.

```
  sudo iptables -t nat -A POSTROUTING -s 192.168.1.21/32 -j SNAT --to-source 10.0.2.15

  # Optional: run this command to print out the NAT table.
  #
  sudo iptables -t nat -L -n -v
```
## Get the routes that AnyConnect manages

  These routes are exposed through the AnyConnect CLI. We need these routes so we can install them
  onto hosts that don't want to run AnyConnect but still want access to the target network(s).

  In my case, the IP address of my gateway VM is 192.168.1.231; use your address instead.
  Run these commands to get the routes installed by the AnyConnect application:

```
  # Get the status file (containing the routes and netmask lengths)
  /opt/cisco/anyconnect/bin/vpn stats > mystatfile.txt

  # Transform the status file into route add commands for linux
  ./transform_to_routes.py mystatfile.txt 192.168.111.231 linux > myRoutes.sh

  # Transform the status file into route add commands for MacOS
  ./transform_to_routes.py mystatfile.txt 192.168.111.231 macOS > myRoutes.sh
```

## Install the routes by running the myRoutes.sh script

  Log onto a host that wants to reach the target network(s) without having to run AnyConnect.
  Do this:

```
  chmod a+x myRoutes.sh
  ./myRoutes.sh

  # For Linux: show the route table.
  #
  route -n

  # For MacOS: show the route table.
  #
  netstat -nr

  # To remove routes without rebooting, do this:
  #
  cat myRoutes.sh | sed 's/add/delete/g' > remove_myRoutes.sh
  chmod a+x remove_myRoutes.sh
  ./remove_myRoutes.sh
```

## Install DNS servers and domainname searches on your hosts

  Now that your hosts have routes and can use the VM gateway to reach the target network(s), you
  want to have some DNS server so you can access the networks as if the host was running AnyConnect.
  These DNS servers were already installed by AnyConnect.  But since these hosts do not run AnyConnect,
  you will have to install this part manually.

  In Linux, this is a matter of augmenting /etc/resolv.conf with ``nameserver x.x.x.x`` where x.x.x.x
  is the IP address of a DNS server for the target network and ``search xxxx.com yyyy.com`` where
  xxxx.com and yyyy.com are DNS domains to search.

  In MacOS, you will have to run the System Preferences app and make similar changes.

## Test connectivity

  To test connectivity, ping or browse to any of the target network(s).  Interaction with the target
  network(s) should be identical to a host actually running AnyConnect.

# Summary

  In summary, you did this:

  * Started AnyConnect and confirmed connectivity to target network(s)
    * Extracted routes from AnyConnect and put them into a script called myRoutes.sh
    * Created a no_myRoutes.sh script to delete routes without rebooting
  * Started a VM gateway with two interfaces (one of which is in NAT mode)
    * Turned on ipv4 forwarding (to act as a router)
    * Added SNAT rules for hosts that want to reach the target networks(s)
  * Configured your hosts
    * Installed routes on the hosts using the myRoutes.sh script
    * Setup DNS and domainname search


  NOTE: the myRoutes.sh and no_myRoutes.sh scripts can be re-used and you can keep the
  VM gatweway running.  This means that to reach the target networks, you do this:

  * Start AnyConnect
  * Configure your host with routes and DNS
