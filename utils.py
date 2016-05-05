# Copyright (c) 2016-2017 Nubosh Inc.

import os, re

class Utils:
    @classmethod
    def ValidateBoolean(cls, text):
        # "1", "0" is valid boolean value
        # "on", "off" is valid boolean value
        # "true", "false" is valid boolean value
        value = text.lower()
        if value in ["1", "on", "true"]:
            return (True, True)
        elif value in ["0", "off", "false"]:
            return (True, False)
        else:
            raise Exception("Unknown boolean value '%s'" % text)

    @classmethod
    def ValidateIP(cls, text):
        rc = re.match("^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$", text)
        if not rc: return False
        ints = map(int, rc.groups())
        largest = 0
        for i in ints:
            if i > 255: return False
            largest = max(largest, i)
        if largest is 0: return False
        return True
    
    @classmethod
    def ValidateNetmask(cls, text):
        rc = re.match("^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$", text)
        if not rc:
            return False
        ints = map(int, rc.groups())
        for i in ints:
            if i > 255:
                return False
        return True

    @classmethod
    def ValidateIPproto(cls, text):
        text = text.lower()
        if not text in ["static", "dhcp", "none"]:
            return False
        return True

    @classmethod
    def ValidateIfaceExists(cls, iface):
        iface = iface.lower()
        if os.path.exists(os.path.join("/sys/class/net", iface)):
            return True
        return False

    @classmethod
    def ValidatePositiveNum(cls, text):
        rc = re.match("^[1-9][0-9]*$", text)
        if not rc:
            return False
        return True