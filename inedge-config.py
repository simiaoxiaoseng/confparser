#!/usr/bin/env python
#
# Copyright (c) 2016-2017 Nubosh Inc.

import sys, os, re
import json
import tempfile

from convertor import *
from interface import *
from service   import *
from routing   import *

JOB_HANDLED = 0
NO_JOB_HANDLER = 1
REDIRECT_TO_SUB_HANDLER = 2

class INConfig:
    def __init__(self, json_conf):
        self.json_conf = json_conf
    
    # private method
    def __clean_old_config_file(self, all_registered_types):
        for typename in all_registered_types.keys():
            dirpath  = INConvertor.GetTargetConfDir(typename)
            filename = INConvertor.GetTargetConfFile(typename)

            abspath = os.path.join(dirpath, filename)
            if os.path.exists(abspath):
                # do not remove old config file in case of any disaster
                os.rename(abspath, abspath + ".bak")

    def __convert(self, typename, typeconf):
        if INConvertor.GetNamedType(typename) == None:
            return NO_JOB_HANDLER

        if INConvertor.RedirectToSubHandler(typename):
            for sub_type, sub_conf in typeconf.items():
                self.__convert(sub_type, sub_conf)
            return REDIRECT_TO_SUB_HANDLER

        INConvertor.InputHandler(typename)(typeconf)

        dirpath = INConvertor.GetTargetConfDir(typename)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        filename = INConvertor.GetTargetConfFile(typename)
        try:
            if INConvertor.ShareConfigFile(typename):
                foutput = open(os.path.join(dirpath, filename), 'a+')
            else:
                foutput = open(os.path.join(dirpath, filename), 'w')
            INConvertor.OutputHandler(typename)(foutput)
        finally:
            foutput.close()

        return JOB_HANDLED

    def Run(self):
        commentsRE = re.compile("^\s*[#|//]")

        json_data = []
        try:
            f = open(self.json_conf, 'r')
            for line in f:
                # NOTE: Json syntax standard does not support comments, here
                # we filter these comments lines and then pass the remaining
                # content to python json library.
                #
                # The comments syntax is simple, the comments line should have
                # a prefix of "#" or "//", see examples.
                if commentsRE.match(line) == None:
                    # all consequent string comparisons by using lower-case 
                    json_data.append(line.lower())
                else:
                    json_data.append("\n")
        finally:
            f.close()

        target_conf = {}
        try:
            f = tempfile.TemporaryFile()
            for line in json_data:
                f.write(line)
            f.seek(0, 0)
            target_conf = json.load(f)
        finally:
            f.close()

        # clean old ones
        self.__clean_old_config_file(INConvertor.ListAllNamedTypes())
        # generate new ones
        for typename, typeconf in target_conf.items():
            self.__convert(typename, typeconf)


if __name__ == "__main__":
    json_conf = ""
    if (len(sys.argv) < 2):
        sys.exit(0)

    json_conf = sys.argv[1]
    if not os.path.exists(json_conf):
        raise Exception("File '%s' not found" % json_conf)

    try:
        INConfig(json_conf).Run()
    except Exception, e:
        raise
