#!/usr/bin/python

# Copyright (c) 2013 EMC Corporation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import xml.dom.minidom
from xml.dom.minidom import Node
from tokenize import generate_tokens
from cStringIO import StringIO

class Parser(object):
    doc = xml.dom.minidom.parse("config.xml")

    def get_list_of_options(self, command):
        command = command.rstrip()
        STRING = 1
        output = []
        L = list(token[STRING] for token in generate_tokens(StringIO(command).readline)
            if token[STRING])
        count = len(L)
        found = 0

        for node in self.doc.getElementsByTagName("command"):
            count = count -1
            if(count == -1):
                output.append(node.getAttribute("name").encode('utf-8'))
           
            #print "COMMAND: " + node.getAttribute("name")
            if(count > -1):
                if(node.getAttribute("name").encode('utf-8')==L[0]):
                    L1 = node.getElementsByTagName("module")
                    count = count - 1
                    for node2 in L1:
                        if(found==1 or found==2):
                            return output
                        if(count == -1):
                            output.append(node2.getAttribute("name").encode('utf-8'))

                        #print "MODULE: " + node2.getAttribute("name")
                        if(count > -1):
                            if(node2.getAttribute("name").encode('utf-8')==L[1]):
                                L2 = node2.getElementsByTagName("operation")
                                count = count - 1
                                for node3 in L2:
                                    if(found==2):
                                        return output
                                    if(count == -1):
                                        if(node3.getAttribute("name").encode('utf-8') != "Noop"):
                                            output.append(node3.getAttribute("name").encode('utf-8'))
                                            found=1
                                        else:
                                            L3 = node3.getElementsByTagName("parameter")
                                            if(len(L3)==0):
                                                count=-2
                                            else:
                                                count = count - 1
                                            for node4 in L3:
                                                if(count == -2):
                                                    output.append(node4.getAttribute("name").encode('utf-8') + " " + "\"<" + node4.getAttribute("metavar") +">\"")
                                                    found=2
                                   
                                   # print "OPERATION: " + node3.getAttribute("name")
                                    if(count > -1):
                                        if(node3.getAttribute("name").encode('utf-8')==L[2]):
                                            L3 = node3.getElementsByTagName("parameter")
                                            if(len(L3)==0):
                                                count=-2
                                            else:
                                                count = count - 1
                                            for node4 in L3:
                                                if(count == -1):
                                                    output.append(node4.getAttribute("name").encode('utf-8') + " " + "\"<" + node4.getAttribute("metavar") +">\"")
                                                    found=2
                                        elif node3.getAttribute("name").encode('utf-8').startswith(L[2]):
                                            output.append(node3.getAttribute("name").encode('utf-8'))
                                             

                            elif node2.getAttribute("name").encode('utf-8').startswith(L[1]):
                                output.append(node2.getAttribute("name").encode('utf-8'))
                                

                elif node.getAttribute("name").encode('utf-8').startswith(L[0]):
                    output.append(node.getAttribute("name").encode('utf-8'))
                            
                                                #print "<" + node4.getAttribute("metavar") +">"
                               
        return output

