# Copyright (c) 2016-2017 Nubosh Inc.

import time

from convertor import *
from utils import *


class Routing:
    def __init__(self, conf_file, redirect_to_sub_handler):
        self.name = "routing"
        self.target_conf_dir = "/etc/quagga"
        self.target_conf_file = conf_file
        self.redirect_to_sub_handler = redirect_to_sub_handler
        self.routing_conf = {}
        self.firewall_conf = {}
        
    # private method
    def __option_valid_or_not(self, option_name, options = self.options):
        if not option_name in options:
            raise Exception("Unknown %s option '%s'" % (self.name, option_name))

    def __output_header(self, output):
        #!
        #! Zebra configuration saved from vtysh/script
        #!   2016/04/20 22:19:19
        #!
        output.write("! \n")
        output.write("! Zebra configuration saved from script\n")
        output.write("!   %s\n" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        output.write("! \n")

    # public handler
    def Input(self, orig_conf):
        pass

    def Output(self, output):
        pass

    def Firewall(self, output):
        pass

    def Register(self):
        handler = {
            "redirect_to_sub_handler": self.redirect_to_sub_handler,
            "share_config_file": False,
            "target_conf_dir": self.target_conf_dir,
            "target_conf_file": self.target_conf_file,
            "input_handler": self.Input,
            "output_handler": self.Output
        }
        INConvertor.RegisterNamedType(self.name, handler)


class RoutingStatic(Routing):
    def __init__(self):
        # NOTE: old style python treats the following statement as invalid
        # super(RoutingStatic, self).__init__("zebra.conf", False)
        Routing.__init__(self, "zebra.conf", False)
        self.name = "static"
        self.options = ["network", "nexthop"]

    
    def Input(self, orig_conf):
        for rulename, ruleconf in orig_conf.items():
            for k, v in ruleconf.items():
                syntax_ok = True
                # NOTE: it might not be a good way to access python private method
                self._Routing__option_valid_or_not(k)
                if k == "network":
                    syntax_ok = Utils.ValidateNetwork(v)
                elif k == "nexthop":
                    syntax_ok = Utils.ValidateIP(v)
                else:
                    pass

                if self.routing_conf.get(rulename, None) == None:
                    self.routing_conf[rulename] = {}
                self.routing_conf[rulename][k] = v

    def Output(self, output):
        #ip route 10.128.1.10/24 2.2.2.2
        #ip route 172.12.0.0/16 1.1.1.1
        
        # NOTE: it might not be a good way to access python private method
        self._Routing__output_header(output)

        for rulename, ruleconf in self.routing_conf.items():
            network = ruleconf.get("network", None)
            if network == None:
                raise Exception("Missing option 'network' for %s" % self.name)
            nexthop = ruleconf.get("nexthop", None)
            if nexthop == None:
                raise Exception("Missing option 'nexthop' for %s" % self.name)
            output.write("ip route %s %s\n" % (network, nexthop))
        output.write("! \n")

class RoutingRIP(Routing):
    def __init__(self):
        # NOTE: old style python treats the following statement as invalid
        # super(RoutingRIP, self).__init__("ripd.conf", False)
        Routing.__init__(self, "ripd.conf", False)
        self.name = "rip"
        self.options = ["update_timer", "timeout", "gc_timer", "rt_kernel", 
                        "rt_co", "rt_static", "rt_ospf"]
        self.sub_options = ["address"]

    def Input(self, orig_conf):
        for k, v in orig_conf.items():
            if isinstance(v, dict):
                pass
            else:
                pass

    def Output(self, output):
        #router rip
        #  timers basic 100 200 60
        #  redistribute kernel
        #  redistribute connected
        #  redistribute static
        #  redistribute ospf
        #  network 172.12.0.0/16
        
        # NOTE: it might not be a good way to access python private method#
        self._Routing__output_header(output)


class RoutingPolicy(Routing):
    def __init__(self):
        # NOTE: old style python treats the following statement as invalid
        # super(RoutingPolicy, self).__init__("firewall", False)
        Routing.__init__(self, "firewall", False)
        self.name = "policy"
        self.target_conf_dir = "/etc/config"


class RoutingOSPF(Routing):
    def __init__(self):
        # NOTE: old style python treats the following statement as invalid
        # super(RoutingOSPF, self).__init__("ospfd.conf", False)
        Routing.__init__(self, "ospfd.conf", False)
        self.name = "ospf"


Routing("routing", True).Register()
RoutingStatic().Register()
RoutingRIP().Register()
RoutingOSPF().Register()
