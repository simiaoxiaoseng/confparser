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

        self.indent = "".join([' ' for i in range(2)])
        
    # private method
    def __option_valid_or_not(self, option_name, options = None):
        if options == None:
            options = self.options
        if not option_name in options:
            raise Exception("Unknown %s option '%s'" % (self.name, option_name))

    def __option_fullname(self, shortname):
        fullname = shortname
        if shortname == "rt_kernel":
            fullname = "redistribute kernel"
        elif shortname == "rt_co":
            fullname = "redistribute connected"
        elif shortname == "rt_static":
            fullname = "redistribute static"
        elif shortname == "rt_ospf":
            fullname = "redistribute ospf"
        elif shortname == "rt_rip":
            fullname = "redistribute rip"
        return fullname

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
                
                if not syntax_ok:
                    raise Exception("Unknown %s value '%s'" % (self.name, v))

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
            output.write("ip route %s %s!\n" % (network, nexthop))
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
            syntax_ok = True
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    self._Routing__option_valid_or_not(sub_k, self.sub_options)
                    if not Utils.ValidateNetwork(sub_v):
                        raise Exception("Unknown %s value '%s'" % (self.name, v))

                    if self.routing_conf.get("network", None) == None:
                        self.routing_conf["network"] = []
                    self.routing_conf["network"].append(sub_v)
            else:
                # NOTE: it might not be a good way to access python private method
                self._Routing__option_valid_or_not(k)
                if k == "update_timer" or k == "timeout" or k == "gc_timer":
                    if not Utils.ValidatePositiveNum(str(v)):
                        raise Exception("Unknown %s value '%s'" % (self.name, v))
                    self.routing_conf[k] = v
                else:
                    enabled = False

                    (syntax_ok, enabled) = Utils.ValidateBoolean(v)
                    if not syntax_ok:
                        raise Exception("Unknown %s value '%s'" % (self.name, v))
                    key = self._Routing__option_fullname(k)
                    self.routing_conf[key] = enabled

    def Output(self, output):
        # router rip
        #   timers basic 100 200 60
        #   redistribute kernel
        #   redistribute connected
        #   redistribute static
        #   redistribute ospf
        #   network 172.12.0.0/16
        #   network 172.69.180.0/24
        padding = self.indent
        
        # NOTE: it might not be a good way to access python private method
        self._Routing__output_header(output)
        
        output.write("router rip\n")
        # Routing table update timer
        update_timer = 30
        if self.routing_conf.get("update_timer", None):
            update_timer = self.routing_conf["update_timer"]
            del self.routing_conf["update_timer"]
        # Routing information timeout
        timeout = 180
        if self.routing_conf.get("timeout", None):
            timeout = self.routing_conf["timeout"]
            del self.routing_conf["timeout"]
        # Garbage collection timer
        gc_timer = 120
        if self.routing_conf.get("gc_timer", None):
            gc_timer = self.routing_conf["gc_timer"]
            del self.routing_conf["gc_timer"]
        output.write("%stimers basic %d %d %d\n" % (padding, update_timer, timeout, gc_timer))

        if self.routing_conf.get("network", None):
            for net in self.routing_conf["network"]:
                output.write("%snetwork %s\n" % (padding, net))
            del self.routing_conf["network"]

        for k, v in self.routing_conf.items():
            if v:
                output.write("%s%s\n" % (padding, k))
        output.write("! \n")



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
        self.options = ["router-id", "default-metric", "rt_kernel", 
                        "rt_co", "rt_static", "rt_ospf"]
        self.sub_options_1 = ["id", "virt-link", "type", "network"]
        self.sub_options_2 = ["ifname", "priority", "hello-intval", 
                              "retran-intval", "passive"]

    # private method
    def __ospf_type_valid_or_not(self, ospf_type):
        return True

    def Input(self, orig_conf):
        for k, v in orig_conf.items():
            syntax_ok = True
            enabled = False

            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    if k.startswith("area"):
                        self._Routing__option_valid_or_not(sub_k, self.sub_options_1)

                        if sub_k == "id":
                            syntax_ok = Utils.ValidateRouteAreaID(str(sub_v))
                        elif sub_k == "virt-link":
                            syntax_ok = Utils.ValidateIP(sub_v)
                        elif sub_k == "network":
                            syntax_ok = Utils.ValidateNetwork(sub_v)
                        elif sub_k == "type":
                            syntax_ok = self.__ospf_type_valid_or_not(sub_v)
                    elif k.startswith("interface"):
                        self._Routing__option_valid_or_not(sub_k, self.sub_options_2)

                        if sub_k == "ifname":
                            # FIXME
                            # syntax_ok = Utils.ValidateIfaceExists(sub_v)
                            pass
                        elif sub_k == "passive":
                            (syntax_ok, enabled) = Utils.ValidateBoolean(str(sub_v))
                        else:
                            syntax_ok = Utils.ValidatePositiveNum(str(sub_v))
                    else:
                        raise Exception("Unknown %s option '%s'" % (self.name, k))

                    if not syntax_ok:
                        raise Exception("Unknown %s value '%s'" % (self.name, sub_v))

                    if self.routing_conf.get(k, None) == None:
                        self.routing_conf[k] = {}
                    if sub_k == "passive":
                        self.routing_conf[k][sub_k] = enabled
                    else:
                        self.routing_conf[k][sub_k] = sub_v
            else:
                # NOTE: it might not be a good way to access python private method
                self._Routing__option_valid_or_not(k)

                key = k
                value = v
                if k == "router-id":
                    syntax_ok = Utils.ValidateIP(str(v)) or Utils.ValidatePositiveNum(str(v))
                    value = str(v)
                elif k == "default-metric":
                    syntax_ok = Utils.ValidatePositiveNum(str(v))
                else:
                    key = self._Routing__option_fullname(k)
                    (syntax_ok, enabled) = Utils.ValidateBoolean(v)
                    value = enabled

                if not syntax_ok:
                    raise Exception("Unknown %s value '%s'" % (self.name, v))
                self.routing_conf[key] = value


    def Output(self, output):
        #!
        #interface eth0
        #  ip ospf hello-interval 54
        #  ip ospf retransmit-interval 350
        #  ip ospf priority 38
        #!
        #!
        #router ospf
        #  ospf router-id 10.1.1.2
        #  redistribute kernel
        #  redistribute rip
        #  passive-interface eth0
        #  area 0.0.0.21 stub no-summary
        #  area 0.0.0.56 nssa translate-candidate
        #  area 2.2.3.4 range 10.2.33.0/24
        #  area 20 virtual-link 1.1.1.1
        #  default-metric 12
        #!
        padding = self.indent
        
        # NOTE: it might not be a good way to access python private method
        self._Routing__output_header(output)

        # Output interface config
        iflist = []
        passive_iflist = []
        for k, v in self.routing_conf.items():
            if k.startswith("interface"):
                if v.get("ifname", None):
                    output.write("interface %s\n" % v["ifname"])
                else:
                    raise Exception("Missing option 'interface.ifname' for %s" % self.name)

                if v.get("hello-intval", None):
                    output.write("%sip ospf hello-interval %d\n" % (padding, v["hello-intval"]))
                if v.get("retran-intval", None):
                    output.write("%sip ospf retransmit-interval %d\n" % (padding, v["retran-intval"]))
                if v.get("priority", None):
                    output.write("%sip ospf priority %d\n" % (padding, v["priority"]))

                output.write("! \n")

                iflist.append(k)
                if v.get("passive", None):
                    if v["passive"]:
                        passive_iflist.append(v["ifname"])

        for ifcfg in iflist:
            del self.routing_conf[ifcfg]

        # Output router config
        output.write("router ospf\n")
        if self.routing_conf.get("router-id", None):
            output.write("%sospf router-id %s\n" % (padding, self.routing_conf["router-id"]))
            del self.routing_conf["router-id"]
        else:
            raise Exception("Missing option 'router-id' for %s" % self.name)

        if self.routing_conf.get("default-metric", None):
            output.write("%sdefault-metric %d\n" % (padding, self.routing_conf["default-metric"]))
            del self.routing_conf["default-metric"]
        else:
            raise Exception("Missing option 'default-metric' for %s" % self.name)

        for ifname in passive_iflist:
            output.write("%spassive-interface %s\n" % (padding, ifname))
        
        # Output ospf area config
        area_list = []
        for k, v in self.routing_conf.items():
            if k.startswith("area"):
                area = "area"
                if v.get("id", None):
                    area = area + " " + v["id"]
                else:
                    raise Exception("Missing option 'area.id' for %s" % self.name)

                if v.get("virt-link", None):
                    area = area + " " + ("virtual-link %s" % v["virt-link"])
                if v.get("network", None):
                    area = area + " " + ("range %s" % v["network"])
                if v.get("type", None):
                    if v["type"] != "normal":
                        area = area + " " + ("%s" % v["type"])

                output.write("%s%s\n" % (padding, area))

                area_list.append(k)

        for area in area_list:
            del self.routing_conf[area]

        # Output routing redistribute config
        for k, v in self.routing_conf.items():
            if v:
                output.write("%s%s\n" % (padding, k))
        output.write("! \n")



Routing("routing", True).Register()
RoutingStatic().Register()
RoutingRIP().Register()
RoutingOSPF().Register()
