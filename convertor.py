# Copyright (c) 2016-2017 Nubosh Inc.

class INConvertor:
    types = {}

    @classmethod
    def Reset(cls):
        cls.types = {}

    @classmethod
    def RegisterNamedType(cls, name, handler):
        handlers = ["interface", "service", "routing"]
        service_handlers = ["ssh", "dhcp", "dns", "ddns", "dns forward"]
        routing_handlers = ["static", "rip", "policy", "ospf"]
        if not name in (handlers + service_handlers + routing_handlers):
            raise Exception("Unknown type handler '%s'" % name)
        cls.types[name] = handler

    @classmethod
    def UnregisterNamedType(cls, name):
        if not name in cls.types.keys():
            raise Exception("Unknown type name '%s'" % name)
        del cls.types[name]

    @classmethod
    def ListAllNamedTypes(cls):
        return cls.types

    @classmethod
    def GetNamedType(cls, name):
        if not name in cls.types.keys():
            return None
        return cls.types[name]

    @classmethod
    def RedirectToSubHandler(cls, name):
        if not name in cls.types.keys():
            raise Exception("Unknown type name '%s'" % name)
        return cls.types[name].get("redirect_to_sub_handler", False)

    @classmethod
    def ShareConfigFile(cls, name):
        if not name in cls.types.keys():
            raise Exception("Unknown type name '%s'" % name)
        return cls.types[name].get("share_config_file", False)

    @classmethod
    def GetTargetConfDir(cls, name):
        if not name in cls.types.keys():
            raise Exception("Unknown type name")
        return cls.types[name].get("target_conf_dir", None)

    @classmethod
    def GetTargetConfFile(cls, name):
        if not name in cls.types.keys():
            raise Exception("Unknown type name")
        return cls.types[name].get("target_conf_file", None)

    @classmethod
    def GetConfigRWMode(cls, name):
        if not name in cls.types.keys():
            raise Exception("Unknown type name")
        return cls.types[name].get("config_rw_mode", None)

    @classmethod
    def GetDepends(cls, name):
        if not name in cls.types.keys():
            raise Exception("Unknown type name")
        return cls.types[name].get("depends", None)

    @classmethod
    def InputHandler(cls, name):
        if not name in cls.types.keys():
            raise Exception("Unknown type name")
        return cls.types[name].get("input_handler", None)

    @classmethod
    def AdditionalInputHandler(cls, name):
        if not name in cls.types.keys():
            raise Exception("Unknown type name")
        return cls.types[name].get("additional_input", None)

    @classmethod
    def OutputHandler(cls, name):
        if not name in cls.types.keys():
            raise Exception("Unknown type name")
        return cls.types[name].get("output_handler", None)
