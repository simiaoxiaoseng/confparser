# Copyright (c) 2016-2017 Nubosh Inc.

import re

from convertor import *
from utils import *

class Service:
    def __init__(self, conf_file, redirect_to_sub_handler, share_config_file):
        self.name = "service"
        self.target_conf_dir = "/etc/config"
        self.target_conf_file = conf_file
        self.redirect_to_sub_handler = redirect_to_sub_handler
        self.share_config_file = share_config_file
        self.service_conf = {}
        self.firewall_conf = {}

        self.indent = "".join([' ' for i in range(8)])
    
    # private method
    def __option_valid_or_not(self, option_name):
        if not option_name in self.options:
            raise Exception("Unknown %s option '%s'" % (self.name, option_name))

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
            "share_config_file": self.share_config_file,
            "target_conf_dir": self.target_conf_dir,
            "target_conf_file": self.target_conf_file,
            "input_handler": self.Input,
            "output_handler": self.Output
        }
        INConvertor.RegisterNamedType(self.name, handler)



class ServiceSSH(Service):
    def __init__(self):
        # NOTE: old style python treats the following statement as invalid
        # super(ServiceSSH, self).__init__("dropbear", False)
        Service.__init__(self, "dropbear", False, False)
        self.name = "ssh"
        self.options = ["enable"]
        
    def Input(self, orig_conf):
        enabled = True

        for k, v in orig_conf.items():
            syntax_ok = True
            # NOTE: it might not be a good way to access python private method
            self._Service__option_valid_or_not(k)
            if k == "enable":
                (syntax_ok, enabled) = Utils.ValidateBoolean(str(v))

            if not syntax_ok:
                raise Exception("Unknown %s value '%s'" % (self.name, v))

            if k == "enable":
                self.service_conf[k] = enabled
            else:
                self.service_conf[k] = v
                
    def Output(self, output):
        output.write("config dropbear\n")

        padding = self.indent
        for k, v in self.service_conf.items():
            value = v
            if isinstance(v, bool):
                value = {True: '1', False: '0'}[v]
            output.write("%s%s\n" % (padding, "option %s '%s'" % (k, value)))
        output.write("\n")



class ServiceDHCP(Service): # share conf with dns
    def __init__(self):
        # NOTE: old style python treats the following statement as invalid
        # super(ServiceDHCP, self).__init__("dhcp", False, True)
        Service.__init__(self, "dhcp", False, True)
        self.name = "dhcp"
        self.options = ["interface", "start", "limit", "option"]

    # private method
    def __dhcp_option(self, option):
        syntax_ok = False
        dhcp_option = ""
        gatewayRE = re.compile("^gateway:\s*(.*)$")
        mtuRE = re.compile("^mtu:\s*(.*)$")

        match = gatewayRE.match(option)
        if match:
            gateway = match.group(1).strip()
            if Utils.ValidateIP(gateway):
                dhcp_option = "3, %s" % gateway
                syntax_ok = True
            return (syntax_ok, dhcp_option)

        match = mtuRE.match(option)
        if match:
            mtu = match.group(1).strip()
            if Utils.ValidatePositiveNum(mtu):
                dhcp_option = "option:mtu, %s" % mtu
                syntax_ok = True
            return (syntax_ok, dhcp_option)

        return (False, "")

    def Input(self, orig_conf):
        for dhcpname, dhcpconf in orig_conf.items():
            for k, v in dhcpconf.items():
                syntax_ok = True
                dhcp_option = ""
                # NOTE: it might not be a good way to access python private method
                self._Service__option_valid_or_not(k)
                if k == "interface":
                    # FIXME
                    # syntax_ok = Utils.ValidateIfaceExists(v)
                    pass
                elif k == "start":
                    syntax_ok = Utils.ValidateIP(v)
                elif k == "limit":
                    syntax_ok = Utils.ValidatePositiveNum(str(v))
                elif k == "option":
                    (syntax_ok, dhcp_option) = self.__dhcp_option(v)
                else:
                    pass

                if not syntax_ok:
                    raise Exception("Unknown %s value '%s'" % (self.name, v))
                
                if self.service_conf.get(dhcpname, None) == None:
                    self.service_conf[dhcpname] = {}
                if k == "option":
                    self.service_conf[dhcpname][k] = dhcp_option
                else:
                    self.service_conf[dhcpname][k] = v

    def Output(self, output):
        for dhcpname, dhcpconf in self.service_conf.items():
            output.write("config dhcp '%s'\n" % dhcpname)

            padding = self.indent
            for k, v in dhcpconf.items():
                value = v
                if k == "option":
                    output.write("%s%s\n" % (padding, "option %s '%s'" % (k, value)))
                else:
                    output.write("%s%s\n" % (padding, "list dhcp_option '%s'" % value))
            output.write("\n")



class ServiceDNS(Service): # share conf with dhcp
    def __init__(self):
        # NOTE: old style python treats the following statement as invalid
        # super(ServiceDNS, self).__init__("dhcp", False, True)
        Service.__init__(self, "dhcp", False, True) # a little tricky
        self.name = "dns"
        self.options = []

    def Input(self, orig_conf):
        pass



Service("service", True, False).Register()
ServiceSSH().Register()
ServiceDHCP().Register()
