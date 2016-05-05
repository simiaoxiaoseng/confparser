# Copyright (c) 2016-2017 Nubosh Inc.

class INConvertor:
    types = {}

    @classmethod
    def Reset(cls):
        cls.types = {}

    @classmethod
    def RegisterNamedType(cls, name, handler):
        handlers = ["interface", "service", "routing"]
        subhandlers = ["ssh", "dhcp"]
        if not name in (handlers + subhandlers):
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
    def InputHandler(cls, name):
        if not name in cls.types.keys():
            raise Exception("Unknown type name")
        return cls.types[name].get("input_handler", None)

    @classmethod
    def OutputHandler(cls, name):
        if not name in cls.types.keys():
            raise Exception("Unknown type name")
        return cls.types[name].get("output_handler", None)