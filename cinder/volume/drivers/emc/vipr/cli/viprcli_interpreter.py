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

import cmd
import common
import commands
from customparser import Parser
from tokenize import generate_tokens
from cStringIO import StringIO

class ViPRInterpreter(cmd.Cmd):
    
    prompt = 'ViPR_CLI> '
    parser = Parser()
    cf = ""
  
    def do_viprcli(self, command):
        #pass
        # Command to be executed
        command = "viprcli " + command
        # Tokenize the command
        STRING = 1
        L2 = list(token[STRING] for token in generate_tokens(StringIO(command).readline)
            if token[STRING])
        # Check if this was a command other than authenticate
        if(L2[1] != "authenticate"):
            # If cf is set then use it else show a message
            if(len(self.cf) != 0):
                command = command + " -cf "+ self.cf
        # run the command
        output = commands.getoutput(command)
        
        # Find the cf information
        if(L2[1] == "authenticate"):
            self.cf = ""
            L1 = list(token[STRING] for token in generate_tokens(StringIO(output).readline)
                if token[STRING])
            cf_length = len(L1) - 8
            for i in range(0, cf_length-1):
                self.cf = self.cf + str(L1[5 + i]) 
        print output
    
    def complete_viprcli(self, text, line, begidx, endidx):
        before_length =  len(line)
        line = line.rstrip()
        after_length =  len(line)
        STRING = 1
        L = list(token[STRING] for token in generate_tokens(StringIO(line).readline)
            if token[STRING])
        count = len(L)
        completions = self.parser.get_list_of_options(line)
        if(count == 2 and (L[1]=="authenticate" or L[1]=="meter" or L[1] == "monitor")):
            output = ""
            for o in self.parser.get_list_of_options(line):
                output = output + o + " "
            if(before_length == after_length):
                output = L[1] + " " + output
            return [output]
        if(count == 3):
            output = ""
            for o in self.parser.get_list_of_options(line):
                output = output + o + " "
            if(before_length == after_length and (L[2] in self.parser.get_list_of_options(L[0] + " " + L[1]))):
                output = L[2] + " " + output
            return [output]    

        return completions

    def emptyline(self):
        return

    def do_exit(self, line):
        return True

# Need to store cf information so that, after crtl+c there is no need to authenticate again
cf_info = ""

def main():
    global cf_info
    try:
        interpreter = ViPRInterpreter()
        if(len(cf_info) > 0):
            interpreter.cf = cf_info
        interpreter.cmdloop()
    except (KeyboardInterrupt):
        print ""
        cf_info=interpreter.cf
        main()
    except (EOFError):
        print ""

if __name__ == '__main__':
        main()
