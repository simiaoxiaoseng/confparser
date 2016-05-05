#!/usr/bin/env python
#
# Copyright (c) 2016-2017 Nubosh Inc.

from convertor import *

class Routing:
    def __init__(self, conf_file):
        self.name = "routing"
        self.target_conf_dir = "/etc/quagga"
        self.target_conf_file = conf_file
        self.routing_conf = {}
        self.firewall_conf = {}

    @staticmethod
    def default_conf():
        pass

    def Input(self, orig_conf):
        pass

    def Output(self, writer):
        pass

    def Firewall(self, writer):
        pass

    def Register(self):
        handler = {
            "target_conf_dir": self.target_conf_dir,
            "target_conf_file": self.target_conf_file,
            "input_handler": self.Input,
            "output_handler": self.Output
        }
        INConvertor.RegisterNamedType(self.name, handler)

class RoutingStatic(Routing):
    def __init__(self):
        super(RoutingStatic, self).__init__("zebra.conf")
        self.name = "static"

class RoutingRIP(Routing):
    def __init__(self):
        super(RoutingRIP, self).__init__("ripd.conf")
        self.name = "rip"

class RoutingOSPF(Routing):
    def __init__(self):
        super(RoutingOSPF, self).__init__("ospfd.conf")
        self.name = "ospf"

RoutingStatic().Register()
RoutingRIP().Register()
RoutingOSPF().Register()
