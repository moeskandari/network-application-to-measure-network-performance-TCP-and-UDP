from mininet.topo import Topo
from mininet.node import Node


class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        if 'routes' in params:
            for (ip, gateway) in params['routes']:
                self.cmd('ip route add {} via {}'.format(ip, gateway))
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class courseworkTopo(Topo):

    def build(self):
        host1 = self.addHost('host1', ip="192.168.0.2/24",
                             defaultRoute='via 192.168.0.1')  # via routwr 1

        host2 = self.addHost('host2', ip="192.168.0.3/24",
                             defaultRoute='via 192.168.0.1')  # via router 1

        host3 = self.addHost('host3', ip="192.168.2.2/24",
                             defaultRoute='via 192.168.2.1')  # via router2

        host4 = self.addHost('host4', ip="192.168.2.3/24",
                             defaultRoute='via 192.168.2.1')  # via router2

        host5 = self.addHost('host5', ip="192.168.3.2/24",
                             defaultRoute='via 192.168.3.1')  # via router 3

        # static router 1
        router1 = self.addHost('router1', cls=LinuxRouter,
                               ip=None,
                               routes=[
                                   ('192.168.3.0/24', '10.10.1.2'),
                                   ('192.168.2.0/24', '10.10.0.1')
                               ])
        # static router 2
        router2 = self.addHost('router2', cls=LinuxRouter,
                               ip=None,
                               routes=[
                                   ('192.168.0.0/24', '10.10.0.2'),
                                   ('10.10.1.0/24', '10.10.0.2'),
                                   ('192.168.3.0/24', '10.10.0.2')
                               ])
        # static router 3
        router3 = self.addHost('router3', cls=LinuxRouter,
                               ip=None,
                               routes=[
                                   ('192.168.0.0/24', '10.10.1.1'),
                                   ('10.10.0.0/24', '10.10.1.1'),
                                   ('192.168.2.0/24', '10.10.1.1')
                               ])

        # switches to the network
        switch1 = self.addSwitch('switch1')
        switch2 = self.addSwitch('switch2')

        # links between the host `h1` and the `s1` switch
        self.addLink(host1, switch1,
                     params1={'ip': '192.168.0.2/24'})

        self.addLink(host2, switch1,
                     params1={'ip': '192.168.0.3/24'})

        self.addLink(host3, switch2,
                     params1={'ip': '192.168.2.2/24'})

        self.addLink(host4, switch2,
                     params1={'ip': '192.168.2.3/24'})

        self.addLink(host5, router3,
                     intfName1='router1-eth0',
                     params1={'ip': '192.168.3.2/24'},
                     params2={'ip': '192.168.3.1/24'}
                     )

        self.addLink(router1, router2,
                     intfName1='router1-eth2',
                     intfName2='router2-eth2',
                     params1={'ip': '10.10.0.2/24'},
                     params2={'ip': '10.10.0.1/24'},
                     delay='10ms',
                     loss=1)

        self.addLink(router1, router3,
                     intfName1='router1-eth3',
                     intfName2='router3-eth2',
                     params1={'ip': '10.10.1.1/24'},  # node 1 prameters
                     params2={'ip': '10.10.1.2/24'},  # node 2 prameters
                     bw=100,  # 100Mbps
                     delay='100ms',
                     loss=0)

        self.addLink(router1, switch1,
                     intfName1='router1-eth1',
                     params1={'ip': '192.168.0.1/24'},
                     )

        self.addLink(router2, switch2,
                     intfName1='router2-eth1',
                     params1={'ip': '192.168.2.1/24'},
                     )


topos = {'courseworkTopo': (lambda: courseworkTopo())}
