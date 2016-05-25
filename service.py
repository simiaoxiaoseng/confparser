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
        self.config_rw_mode = WRITE_A_NEW_FILE
        self.depends = [] # some service may depend on others, e.g. dns & dhcp
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

    def AdditionalInput(self, conf_lines):
        pass

    def Output(self, output):
        pass

    def Firewall(self, output):
        pass

    def Register(self):
        handler = {
            "redirect_to_sub_handler": self.redirect_to_sub_handler,
            "share_config_file": self.share_config_file,
            "config_rw_mode": self.config_rw_mode,
            "depends": self.depends,
            "target_conf_dir": self.target_conf_dir,
            "target_conf_file": self.target_conf_file,
            "input_handler": self.Input,
            "additional_input": self.AdditionalInput,
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
        
    # public handler
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



class ServiceDHCP(Service):
    def __init__(self):
        # NOTE: old style python treats the following statement as invalid
        # super(ServiceDHCP, self).__init__("dhcp", False, False)
        Service.__init__(self, "dhcp", False, False)
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
    
    def __output_header(self, output):
        padding = self.indent

        header_lines = "option domainneeded '1',\
                option boguspriv '1',\
                option filterwin2k '0',\
                option localise_queries '1',\
                option rebind_protection '1',\
                option rebind_localhost '1',\
                option local '/lan/',\
                option domain 'lan',\
                option expandhosts '1',\
                option nonegcache '0',\
                option authoritative '1',\
                option readethers '1',\
                option leasefile '/tmp/dhcp.leases',\
                option resolvfile '/tmp/resolv.conf.auto',\
                option localservice '1'"

        output.write("config dnsmasq\n")
        for line in header_lines.split(','):
            line = line.strip()
            output.write("%s%s\n" % (padding, line))
        output.write("\n")

    # public handler
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
        self.__output_header(output)

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



class ServiceDNS(Service):
    def __init__(self):
        # NOTE: old style python treats the following statement as invalid
        # super(ServiceDNS, self).__init__("dns", False, False)
        Service.__init__(self, "dns", False, False) # a little tricky
        self.name = "dns"
        self.target_conf_dir = "/etc"
        self.target_conf_file = "resolv.conf"
        self.options = ["server1", "server2", "server3"]
        
    # public handler
    def Input(self, orig_conf):
        for k, v in orig_conf.items():
            syntax_ok = True
            # NOTE: it might not be a good way to access python private method
            self._Service__option_valid_or_not(k)

            syntax_ok = Utils.ValidateIP(v)
            if not syntax_ok:
                raise Exception("Unknown %s value '%s'" % (self.name, v))
            self.service_conf[k] = v

    def Output(self, output):
        for k, v in self.service_conf.items():
            output.write("nameserver %s\n" % v)



class ServiceDNSForward(Service):
    def __init__(self):
        # NOTE: old style python treats the following statement as invalid
        # super(ServiceDNSForward, self).__init__("dns forward", False, False, "rw")
        Service.__init__(self, "dns forward", False, False)
        self.name = "dns forward"
        self.target_conf_file = "dhcp"
        self.config_rw_mode = UPDATE_AN_EXISTING_FILE
        self.depends.append("dhcp") # dns forward has to depend on dhcp
        self.options = ["server1", "server2", "server3"]

        self.lines = None

    # private method
    def __dnsmasq_conf_line(self, line):
        keywordRE = re.compile("config.*dnsmasq")
        if keywordRE.match(line):
            return True
        else:
            return False
    
    def __output_header(self, output):
        padding = self.indent

        header_lines = "option domainneeded '1',\
                option boguspriv '1',\
                option filterwin2k '0',\
                option localise_queries '1',\
                option rebind_protection '1',\
                option rebind_localhost '1',\
                option local '/lan/',\
                option domain 'lan',\
                option expandhosts '1',\
                option nonegcache '0',\
                option authoritative '1',\
                option readethers '1',\
                option leasefile '/tmp/dhcp.leases',\
                option resolvfile '/tmp/resolv.conf.auto',\
                option localservice '1'"

        output.write("config dnsmasq\n")
        for line in header_lines.split(','):
            line = line.strip()
            output.write("%s%s\n" % (padding, line))

    # public handler
    def Input(self, orig_conf):
        for k, v in orig_conf.items():
            syntax_ok = True
            # NOTE: it might not be a good way to access python private method
            self._Service__option_valid_or_not(k)

            syntax_ok = Utils.ValidateIP(v)
            if not syntax_ok:
                raise Exception("Unknown %s value '%s'" % (self.name, v))
            self.service_conf[k] = v

    def AdditionalInput(self, conf_lines):
        self.lines = conf_lines

    def Output(self, output):
        padding = self.indent

        # tricky code
        newconf = True
        if self.lines != None:
            for line in self.lines:
                if self.__dnsmasq_conf_line(line):
                    newconf = False
                    break

        if newconf:
            self.__output_header(output)
            for k, v in self.service_conf.items():
                output.write("%s%s\n" % (padding, "list server '%s'" % v))
            output.write("\n")
        else:
            for line in self.lines:
                output.write(line)
                if self.__dnsmasq_conf_line(line):
                    for k, v in self.service_conf.items():
                        output.write("%s%s\n" % (padding, "list server '%s'" % v))
                    self.service_conf = {}



class ServiceDDNS(Service):
    def __init__(self):
        # NOTE: old style python treats the following statement as invalid
        # super(ServiceDDNS, self).__init__("ddns", False, False)
        Service.__init__(self, "ddns", False, False)
        self.name = "ddns"
        self.options = ["provider", "domain", "username", "password", 
                        "interface", "enabled", "use_https"]

    # private method
    def __output_header(self, output):
        padding = self.indent

        header_lines = "option date_format '%F %R',\
                option log_lines '500',\
                option allow_local_ip '0'"

        output.write("config ddns \"global\"\n")
        for line in header_lines.split(','):
            line = line.strip()
            output.write("%s%s\n" % (padding, line))
        output.write("\n")
    
    # public handler
    def Input(self, orig_conf):
        for k, v in orig_conf.items():
            enabled = False

            syntax_ok = True
            # NOTE: it might not be a good way to access python private method
            self._Service__option_valid_or_not(k)

            if k in ["enabled", "use_https"]:
                (syntax_ok, enabled) = Utils.ValidateBoolean(str(v))
            if not syntax_ok:
                raise Exception("Unknown %s value '%s'" % (self.name, v))

            if k in ["enabled", "use_https"]:
                self.service_conf[k] = enabled
            elif k == "provider":
                self.service_conf["service_name"] = v
            else:
                self.service_conf[k] = v

    def Output(self, output):
        self.__output_header(output)
        
        padding = self.indent

        output.write("config service 'myddns_ipv4'\n")
        for k, v in self.service_conf.items():
            value = v
            if isinstance(v, bool):
                value = {True: '1', False: '0'}[v]
            else:
                pass
            output.write("%s%s\n" % (padding, "option %s '%s'" % (k, value)))
        output.write("\n")



Service("service", True, False).Register()
ServiceSSH().Register()
ServiceDHCP().Register()
ServiceDNS().Register()
ServiceDDNS().Register()
ServiceDNSForward().Register()
