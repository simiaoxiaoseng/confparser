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
from utils     import *

JOB_HANDLED = 0
NO_JOB_HANDLER = 1

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

    def __figure_out_dependency(self, target_conf):
        priority_map = []
        keys = target_conf.keys()
        # we do not check if there is a dependency loop
        for typename in keys:
            if INConvertor.GetNamedType(typename) == None:
                continue

            if not typename in priority_map:
                priority_map.append(typename)

            depends = INConvertor.GetDepends(typename)
            if depends != None and len(depends) != 0:
                for depend in depends:
                    if depend in keys:
                        if not depend in priority_map:
                            priority_map.insert(priority_map.index(typename), depend)
                        else:
                            priority_map.remove(depend)
                            priority_map.insert(priority_map.index(typename), depend)
        return priority_map

    def __convert(self, typename, typeconf):
        if INConvertor.GetNamedType(typename) == None:
            return NO_JOB_HANDLER

        if INConvertor.RedirectToSubHandler(typename):
            for sub_type in self.__figure_out_dependency(typeconf):
                sub_conf = typeconf[sub_type]
                self.__convert(sub_type, sub_conf)
            return JOB_HANDLED

        INConvertor.InputHandler(typename)(typeconf)

        dirpath = INConvertor.GetTargetConfDir(typename)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        filename = INConvertor.GetTargetConfFile(typename)

        foutput = None
        try:
            if INConvertor.ShareConfigFile(typename):
                foutput = open(os.path.join(dirpath, filename), 'a+')
            else:
                rwmode = INConvertor.GetConfigRWMode(typename)
                if rwmode == WRITE_A_NEW_FILE:
                    foutput = open(os.path.join(dirpath, filename), 'w')
                elif rwmode == UPDATE_AN_EXISTING_FILE:
                    if os.path.exists(os.path.join(dirpath, filename)):
                        finput = open(os.path.join(dirpath, filename), 'r')
                        INConvertor.AdditionalInputHandler(typename)(finput.readlines())
                        finput.close()

                    foutput = open(os.path.join(dirpath, filename), 'w')
                else: # rwmode is None
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
        for typename in self.__figure_out_dependency(target_conf):
            typeconf = target_conf[typename]
            self.__convert(typename, typeconf)
        
if __name__ == "__main__":
    json_conf = ""
    if (len(sys.argv) < 2):
        sys.exit(1)

    json_conf = sys.argv[1]
    if not os.path.exists(json_conf):
        raise Exception("File '%s' not found" % json_conf)

    try:
        INConfig(json_conf).Run()
    except Exception, e:
        raise
