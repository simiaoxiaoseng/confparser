# Copyright (c) 2016-2017 Nubosh Inc.

from convertor import *
from utils import *

class Interface:
    def __init__(self):
        self.name = "interface"
        self.target_conf_dir = "/etc/config"
        self.target_conf_file = "network"
        self.interface_conf = {}
        self.firewall_conf = {}

        self.indent = "".join([' ' for i in range(8)])

    # private method
    def __option_valid_or_not(self, option_name):
        options = ["ifname", "proto", "ipaddr", "netmask", "gateway",
                   "access", "stp", "type"]
        if not option_name in options:
            raise Exception("Unknown interface option '%s'" % option_name)

    def __firewall_input(self, name, v):
        valid_protocol = ["telnet", "web", "ssh", "ping", "snmp"]
        for protocol in v:
            if not protocol in valid_protocol:
                raise Exception("Unknown interface protocol '%s'" % protocol)
        self.firewall_conf[name] = v

    def __interface_input(self, name, k, v):
        stp_enabled = False

        syntax_ok = True
        if k in ["ipaddr", "gateway"]:
            syntax_ok = Utils.ValidateIP(v)
        elif k == "netmask":
            syntax_ok = Utils.ValidateNetmask(v)
        elif k == "proto":
            syntax_ok = Utils.ValidateIPproto(v)
        elif k == "ifname":
            for iface in v:
                # FIXME
                # syntax_ok = Utils.ValidateIfaceExists(iface)
                pass
        elif k == "stp":
            (syntax_ok, stp_enabled) = Utils.ValidateBoolean(str(v))
        elif k == "type":
            syntax_ok = (v == "bridge")
        if not syntax_ok:
            raise Exception("Unknown interface value '%s'" % v)

        if self.interface_conf.get(name, None) == None:
            self.interface_conf[name] = {}
        if k == "stp":
            self.interface_conf[name][k] = stp_enabled
        else:
            self.interface_conf[name][k] = v

    def __output_loopback_inf(self, output):
        padding = self.indent

        output.write("config interface 'loopback'\n")
        output.write("%s%s\n" % (padding, "option ifname '%s'" % "lo"))
        output.write("%s%s\n" % (padding, "option proto '%s'" % "static"))
        output.write("\n")

    # public handler
    def Input(self, orig_conf):
        for ifname, conf in orig_conf.items():
            for k, v in conf.items():
                self.__option_valid_or_not(k)
                if k == "access":
                    self.__firewall_input(ifname, v)
                else:
                    self.__interface_input(ifname, k, v)

    def Output(self, output):
        self.__output_loopback_inf(output)

        padding = self.indent
        for ifname, conf in self.interface_conf.items():
            output.write("config interface '%s'\n" % ifname)
            for k, v in conf.items():
                value = v
                if isinstance(v, bool):
                    value = {True: '1', False: '0'}[v]
                elif isinstance(v, list):
                    value = " ".join(v)
                else:
                    pass
                output.write("%s%s\n" % (padding, "option %s '%s'" % (k, value)))
            output.write("\n")

    def Firewall(self):
        for ifname, conf in self.firewall_conf.items():
            pass

    def Register(self):
        handler = {
            "redirect_to_sub_handler": False,
            "share_config_file": False,
            "target_conf_dir": self.target_conf_dir,
            "target_conf_file": self.target_conf_file,
            "input_handler": self.Input,
            "output_handler": self.Output
        }
        INConvertor.RegisterNamedType(self.name, handler)

Interface().Register()
