#! /usr/bin/python
#******************************************************************************

#    OpenAirInterface 
#    Copyright(c) 1999 - 2014 Eurecom

#    OpenAirInterface is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.


#    OpenAirInterface is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with OpenAirInterface.The full GNU General Public License is 
#   included in this distribution in the file called "COPYING". If not, 
#   see <http://www.gnu.org/licenses/>.

#  Contact Information
#  OpenAirInterface Admin: openair_admin@eurecom.fr
#  OpenAirInterface Tech : openair_tech@eurecom.fr
#  OpenAirInterface Dev  : openair4g-devel@lists.eurecom.fr
  
#  Address      : Eurecom, Campus SophiaTech, 450 Route des Chappes, CS 50193 - 06904 Biot Sophia Antipolis cedex, FRANCE

# *******************************************************************************/

# \file test01.py
# \brief test 01 for OAI
# \author Navid Nikaein
# \date 2013 - 2015
# \version 0.1
# @ingroup _test

import tempfile
import threading
import sys
import traceback
import wave
import os
import time
import datetime
import getpass
import math #from time import clock 
import xml.etree.ElementTree as ET

import log
import case01
import case02
import case03
import case04
import case05

from  openair import *

import paramiko

def write_file(filename, string, mode="w"):
   text_file = open(filename, mode)
   text_file.write(string)
   text_file.close()
   

def sftp_module (username, password, hostname, ports, localfile, remotefile, logfile, operation):
   localD = localfile
   remoteD = remotefile
   #fd, paramiko_logfile  = tempfile.mkstemp()
   #res = os.close(fd )
   #paramiko logfile path should not be changed with multiple calls. The logs seem to in first file regardless
   paramiko_logfile = os.path.expandvars('$OPENAIR_DIR/cmake_targets/autotests/log/paramiko.log')
   error = ""
   try:
      res=os.system(' echo > ' + paramiko_logfile)
      paramiko.util.log_to_file(paramiko_logfile)
      transport = paramiko.Transport((hostname, ports))
      transport.connect(username = username, password = password)
      sftp = paramiko.SFTPClient.from_transport(transport)
      if operation == "put":
        sftp.put(remotepath=remoteD, localpath=localD)
      elif operation == "get":
        sftp.get(remotepath=remoteD, localpath=localD)
      else :
        print "sftp_module: unidentified operation. Exiting now"
        print "hostname = " + hostname
        print "ports = " + ports
        print "localfile = " + localfile
        print "remotefile = " + remotefile
        print "logfile = " + logfile
        print "operation = " + operation
        sys.exit()
        sftp.close()
        transport.close()
   except Exception, e:
        error = ' In function: ' + sys._getframe().f_code.co_name + ': *** Caught exception: '  + str(e.__class__) + " : " + str( e)
        error = error + '\n username = ' + username + '\n hostname = ' + hostname + '\n localfile = ' + localfile + '\n remotefile = ' + remotefile + '\n operation = ' + operation + '\nlogfile = ' + logfile + '\n ports = ' + str(ports) + '\n'  
        error = error + traceback.format_exc()
   
   res = os.system('\n echo \'SFTP Module Log for Machine: <' + hostname + '> starts...\' >> ' + logfile + ' 2>&1 ')
   res = os.system('cat ' + paramiko_logfile + ' >> ' + logfile + ' 2>&1 \n')
   write_file(logfile, error, "a")
   res = os.system('\n echo \'SFTP Module Log for Machine: <' + hostname + '> ends...\' >> ' + logfile + ' 2>&1 \n')

def finalize_deploy_script (timeout_cmd, terminate_missing_procs='True'):
  cmd = 'declare -i timeout_cmd='+str(timeout_cmd) + '\n'
  if terminate_missing_procs == 'True':
    cmd = cmd +  """
    #The code below checks if one the processes launched in background has crashed.
    #If it does, then the code below terminates all the child processes created by this script
    declare -i wakeup_interval=1
    declare -i step=0
    echo \"Array pid =  ${array_exec_pid[@]}\"
    while [ "$step" -lt "$timeout_cmd" ]
      do
       declare -i break_while_loop=0
       #Iterate over each process ID in array_exec_pid
       for i in "${array_exec_pid[@]}"
       do
        numchild=`pstree -p $i | perl -ne 's/\((\d+)\)/print " $1"/ge' |wc -w`
        echo "PID = $i, numchild = $numchild"
        if  [ "$numchild" -eq "0" ] ; then
            echo "Process ID $i has finished unexpectedly. Now preparing to kill all the processes "
            break_while_loop=1
            break
        fi
     done
    if  [ "$break_while_loop" -eq "1" ] ; then
             break
    fi
    step=$(( step + wakeup_interval ))
    sleep $wakeup_interval
    done
    echo "Final time step (Duration of test case) = $step "
    """
  else:
    #We do not terminate the script if one of the processes has existed prematurely
    cmd = cmd + 'sleep ' + str(timeout_cmd) + '\n'
  
  return cmd

def update_config_file(oai, config_string, logdirRepo, python_script):
  if config_string :
    stringArray = config_string.splitlines()
    cmd=""
    #python_script = '$OPENAIR_DIR/targets/autotests/tools/search_repl.py'
    for string in stringArray:
       #split the string based on space now
       string1=string.split()
       cmd = cmd + 'python ' + python_script + ' ' + logdirRepo+'/'+string1[0] + '  ' + string1[1] +  ' '+ string1[2] + '\n'
       #cmd = cmd + 'perl -p -i  -e \'s/'+ string1[1] + '\\s*=\\s*"\\S*"\\s*/' + string1[1] + ' = "' + string1[2] +'"' + '/g\'   ' + logdirRepo + '/' +string1[0] + '\n'
    return cmd
    #result = oai.send_recv(cmd)


 
#Function to clean old programs that might be running from earlier execution
#oai - parameter for making connection to machine
#programList - list of programs that must be terminated before execution of any test case 
def cleanOldPrograms(oai, programList, CleanUpAluLteBox):
  cmd = 'killall -q -r ' + programList
  result = oai.send(cmd, True)
  print "Killing old programs..." + result
  programArray = programList.split()
  programListJoin = '|'.join(programArray)
  cmd = cleanupOldProgramsScript + ' ' + '\''+programListJoin+'\''
  #result = oai.send_recv(cmd)
  #print result
  result = oai.send_expect_false(cmd, 'Match found', False)
  print result
  res=oai.send_recv(CleanUpAluLteBox, True)


class myThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        print "Starting " + self.name


class oaiThread (threading.Thread):
    def __init__(self, threadID, name, oai, cmd, sudo, timeout):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        #self.counter = counter
        self.oai = oai
        self.cmd = cmd
        self.sudo = sudo
        self.timeout = timeout
    def run(self):
        print "Starting " + self.name
        result = self.oai.send_recv(self.cmd, self.sudo, self.timeout)
        print "result = " + result
        print "Exiting " + self.name

def addsudo (cmd, password=""):
  cmd = 'echo \'' + password + '\' | sudo -S -E bash -c \' ' + cmd + '\' '
  return cmd
  
#Function to handle test case class : lte-softmodem
def handle_testcaseclass_softmodem (testcase, oldprogramList, oai_list, logdirOAI5GRepo , logdirOpenaircnRepo, MachineList, password, CleanUpAluLteBox):
  #We ignore the password sent to this function for secuirity reasons for password present in log files
  #It is recommended to add a line in /etc/sudoers that looks something like below. The line below will run sudo without password prompt
  # your_user_name ALL=(ALL:ALL) NOPASSWD: ALL
  mypassword=''
  #addsudo = 'echo \'' + mypassword + '\' | sudo -S -E '
  addpass = 'echo \'' + mypassword + '\' | '
  user = getpass.getuser()
  testcasename = testcase.get('id')
  timeout_cmd = testcase.findtext('TimeOut_cmd',default='')
  timeout_cmd = int(float(timeout_cmd))
  #Timeout_thread is more than that of cmd to have room for compilation time, etc
  timeout_thread = timeout_cmd + 300 
  nruns = testcase.findtext('nruns',default='')
  nruns = int(float(nruns))

  eNBMachine = testcase.findtext('eNB',default='')
  eNB_config_file = testcase.findtext('eNB_config_file',default='')
  eNB_compile_prog = testcase.findtext('eNB_compile_prog',default='')
  eNB_compile_prog_args = testcase.findtext('eNB_compile_prog_args',default='')
  eNB_pre_exec = testcase.findtext('eNB_pre_exec',default='')
  eNB_pre_exec_args = testcase.findtext('eNB_pre_exec_args',default='')
  eNB_main_exec = testcase.findtext('eNB_main_exec',default='')
  eNB_main_exec_args = testcase.findtext('eNB_main_exec_args',default='')
  eNB_traffic_exec = testcase.findtext('eNB_traffic_exec',default='')
  eNB_traffic_exec_args = testcase.findtext('eNB_traffic_exec_args',default='')
  eNB_terminate_missing_procs = testcase.findtext('eNB_terminate_missing_procs',default='True')

  UEMachine = testcase.findtext('UE',default='')
  UE_config_file = testcase.findtext('UE_config_file',default='')
  UE_compile_prog = testcase.findtext('UE_compile_prog',default='')
  UE_compile_prog_args = testcase.findtext('UE_compile_prog_args',default='')
  UE_pre_exec = testcase.findtext('UE_pre_exec',default='')
  UE_pre_exec_args = testcase.findtext('UE_pre_exec_args',default='')
  UE_main_exec = testcase.findtext('UE_main_exec',default='')
  UE_main_exec_args = testcase.findtext('UE_main_exec_args',default='')
  UE_traffic_exec = testcase.findtext('UE_traffic_exec',default='')
  UE_traffic_exec_args = testcase.findtext('UE_traffic_exec_args',default='')
  UE_terminate_missing_procs = testcase.findtext('UE_terminate_missing_procs',default='True')

  EPCMachine = testcase.findtext('EPC',default='')
  EPC_config_file = testcase.findtext('EPC_config_file',default='')
  EPC_compile_prog = testcase.findtext('EPC_compile_prog',default='')
  EPC_compile_prog_args = testcase.findtext('EPC_compile_prog_args',default='')
  HSS_compile_prog = testcase.findtext('HSS_compile_prog',default='')
  HSS_compile_prog_args = testcase.findtext('HSS_compile_prog_args',default='')
  
  EPC_pre_exec= testcase.findtext('EPC_pre_exec',default='')
  EPC_pre_exec_args = testcase.findtext('EPC_pre_exec_args',default='')  
  EPC_main_exec= testcase.findtext('EPC_main_exec',default='')
  EPC_main_exec_args = testcase.findtext('EPC_main_exec_args',default='')  
  HSS_main_exec= testcase.findtext('HSS_main_exec',default='')
  HSS_main_exec_args = testcase.findtext('HSS_main_exec_args',default='')  
  EPC_traffic_exec = testcase.findtext('EPC_traffic_exec',default='')
  EPC_traffic_exec_args = testcase.findtext('EPC_traffic_exec_args',default='')
  EPC_terminate_missing_procs = testcase.findtext('EPC_terminate_missing_procs',default='True')

  index_eNBMachine = MachineList.index(eNBMachine)
  index_UEMachine = MachineList.index(UEMachine)
  index_EPCMachine = MachineList.index(EPCMachine)
  oai_eNB = oai_list[index_eNBMachine]
  oai_UE = oai_list[index_UEMachine]
  
  #We need to create two ssh sessions to avoid race conditions 
  if index_eNBMachine == index_EPCMachine:
     oai_EPC = openair('localdomain', EPCMachine)
     oai_EPC.connect(user,password)
  else:
     oai_EPC = oai_list[index_EPCMachine]
  cleanOldPrograms(oai_eNB, oldprogramList, CleanUpAluLteBox)
  cleanOldPrograms(oai_UE, oldprogramList, CleanUpAluLteBox)
  cleanOldPrograms(oai_EPC, oldprogramList, CleanUpAluLteBox)
  logdir_eNB = logdirOAI5GRepo+'/cmake_targets/autotests/log/'+ testcasename
  logdir_UE =  logdirOAI5GRepo+'/cmake_targets/autotests/log/'+ testcasename
  logdir_EPC = logdirOpenaircnRepo+'/TEST/autotests/log/'+ testcasename
  logdir_local = os.environ.get('OPENAIR_DIR')
  if logdir_local is None:
     print "Environment variable OPENAIR_DIR not set correctly"
     sys.exit()
   
  #Make the log directory of test case
  #cmd = 'mkdir -p ' + logdir_eNB
  #result = oai_eNB.send_recv(cmd)
  #cmd = 'mkdir -p ' +  logdir_UE
  #result = oai_UE.send_recv(cmd)
  #cmd = 'mkdir -p ' + logdir_EPC
  #result = oai_EPC.send_recv(cmd)
  
  print "Updating the config files for ENB/UE/EPC..."
  #updating the eNB/UE/EPC configuration file from the test case 
  #update_config_file(oai_eNB, eNB_config_file, logdirOAI5GRepo)
  #update_config_file(oai_UE, UE_config_file, logdirOAI5GRepo)
  #update_config_file(oai_EPC, EPC_config_file, logdirOpenaircnRepo)
  
  for run in range(0,nruns):
    logdir_eNB = logdirOAI5GRepo+'/cmake_targets/autotests/log/'+ testcasename + '/run_' + str(run)
    logdir_UE =  logdirOAI5GRepo+'/cmake_targets/autotests/log/'+ testcasename + '/run_' + str(run)
    logdir_EPC = logdirOpenaircnRepo+'/TEST/autotests/log/'+ testcasename + '/run_' + str(run)
    logdir_local_testcase = logdir_local + '/cmake_targets/autotests/log/'+ testcasename + '/run_' + str(run)
    #Make the log directory of test case
    cmd = 'rm -fr ' + logdir_eNB + ' ; mkdir -p ' + logdir_eNB
    result = oai_eNB.send_recv(cmd)
    cmd = 'rm -fr ' + logdir_UE + ' ; mkdir -p ' +  logdir_UE
    result = oai_UE.send_recv(cmd)
    cmd = 'rm -fr ' + logdir_EPC + '; mkdir -p ' + logdir_EPC
    result = oai_EPC.send_recv(cmd)
    cmd = ' rm -fr ' + logdir_local_testcase + ' ; mkdir -p ' + logdir_local_testcase
    result = os.system(cmd)
    
    logfile_compile_eNB = logdir_eNB + '/eNB_compile' + '_' + str(run) + '_.log'
    logfile_exec_eNB = logdir_eNB + '/eNB_exec' + '_' + str(run) + '_.log'
    logfile_pre_exec_eNB = logdir_eNB + '/eNB_pre_exec' + '_' + str(run) + '_.log'
    logfile_traffic_eNB = logdir_eNB + '/eNB_traffic' + '_' + str(run) + '_.log'
    logfile_task_eNB_out = logdir_eNB + '/eNB_task_out' + '_' + str(run) + '_.log'
    logfile_task_eNB = logdir_local_testcase + '/eNB_task' + '_' + str(run) + '_.log'
    task_eNB = ' ( \n'
    task_eNB = task_eNB + 'cd ' + logdirOAI5GRepo + ' ; source oaienv ; source cmake_targets/tools/build_helper \n'
    task_eNB = task_eNB + 'env |grep OPENAIR  \n'
    task_eNB = task_eNB + update_config_file(oai_eNB, eNB_config_file, logdirOAI5GRepo, '$OPENAIR_DIR/cmake_targets/autotests/tools/search_repl.py') + '\n'
    if eNB_compile_prog != "":
       task_eNB  = task_eNB +  ' ( ' + eNB_compile_prog + ' '+ eNB_compile_prog_args + ' ) > ' + logfile_compile_eNB + ' 2>&1 \n'
    if eNB_pre_exec != "":
       task_eNB  = task_eNB +  ' ( ' + eNB_pre_exec + ' '+ eNB_pre_exec_args + ' ) > ' + logfile_pre_exec_eNB + ' 2>&1 \n'
    if eNB_main_exec != "":
       task_eNB = task_eNB + ' ( ' + addsudo(eNB_main_exec + ' ' + eNB_main_exec_args, mypassword) + ' ) > ' + logfile_exec_eNB + ' 2>&1 & \n'
       task_eNB = task_eNB + 'array_exec_pid+=($!) \n'
       task_eNB = task_eNB + 'echo eNB_main_exec PID = $! \n'
    if eNB_traffic_exec != "":
       task_eNB = task_eNB + ' ( ' + eNB_traffic_exec + ' ' + eNB_traffic_exec_args + ' ) > ' + logfile_traffic_eNB + ' 2>&1 & \n '
       task_eNB = task_eNB + 'array_exec_pid+=($!) \n'
       task_eNB = task_eNB + 'echo eNB_traffic_exec PID = $! \n'
    #terminate the eNB test case after timeout_cmd seconds
    task_eNB  = task_eNB + finalize_deploy_script (timeout_cmd, eNB_terminate_missing_procs) + ' \n'
    #task_eNB  = task_eNB + 'sleep ' +  str(timeout_cmd) + ' \n'
    task_eNB  = task_eNB + 'handle_ctrl_c' + '\n' 
    task_eNB  = task_eNB + ' ) > ' + logfile_task_eNB_out + ' 2>&1  '
    write_file(logfile_task_eNB, task_eNB, mode="w")

    #task_eNB =  'echo \" ' + task_eNB + '\" > ' + logfile_script_eNB + ' 2>&1 ; ' + task_eNB 
    logfile_compile_UE = logdir_UE + '/UE_compile' + '_' + str(run) + '_.log'
    logfile_exec_UE = logdir_UE + '/UE_exec' + '_' + str(run) + '_.log'
    logfile_pre_exec_UE = logdir_UE + '/UE_pre_exec' + '_' + str(run) + '_.log'
    logfile_traffic_UE = logdir_UE + '/UE_traffic' + '_' + str(run) + '_.log'    
    logfile_task_UE_out = logdir_UE + '/UE_task_out' + '_' + str(run) + '_.log'
    logfile_task_UE = logdir_local_testcase + '/UE_task' + '_' + str(run) + '_.log'
    task_UE = ' ( \n'
    task_UE = task_UE + 'array_exec_pid=()' + '\n'
    task_UE = task_UE + 'cd ' + logdirOAI5GRepo + '\n'  
    task_UE = task_UE + 'source oaienv \n'
    task_UE = task_UE + 'source cmake_targets/tools/build_helper \n'
    task_UE = task_UE + 'env |grep OPENAIR  \n'
    task_UE = task_UE + update_config_file(oai_UE, UE_config_file, logdirOAI5GRepo, '$OPENAIR_DIR/cmake_targets/autotests/tools/search_repl.py') + '\n'
    if UE_compile_prog != "":
       task_UE = task_UE + ' ( ' + UE_compile_prog + ' '+ UE_compile_prog_args + ' ) > ' + logfile_compile_UE + ' 2>&1 \n'
    if UE_pre_exec != "":
       task_UE  = task_UE +  ' ( ' + UE_pre_exec + ' '+ UE_pre_exec_args + ' ) > ' + logfile_pre_exec_UE + ' 2>&1 \n'
    if UE_main_exec != "":
       task_UE = task_UE + ' ( ' + addsudo(UE_main_exec + ' ' + UE_main_exec_args, mypassword)  + ' ) > ' + logfile_exec_UE + ' 2>&1 & \n'
       task_UE = task_UE + 'array_exec_pid+=($!) \n'
       task_UE = task_UE + 'echo UE_main_exec PID = $! \n'
    if UE_traffic_exec != "":
       task_UE = task_UE + ' ( ' + UE_traffic_exec + ' ' + UE_traffic_exec_args + ' ) >' + logfile_traffic_UE + ' 2>&1 & \n'
       task_UE = task_UE + 'array_exec_pid+=($!) \n'
       task_UE = task_UE + 'echo UE_traffic_exec PID = $! \n'
    #terminate the UE test case after timeout_cmd seconds
    task_UE  = task_UE + finalize_deploy_script (timeout_cmd, UE_terminate_missing_procs) + ' \n'
    #task_UE  = task_UE + 'sleep ' +  str(timeout_cmd) + ' \n'
    task_UE  = task_UE + 'handle_ctrl_c' + '\n' 
    task_UE  = task_UE + ' ) > ' + logfile_task_UE_out + ' 2>&1 '
    write_file(logfile_task_UE, task_UE, mode="w")
    #task_UE = 'echo \" ' + task_UE + '\" > ' + logfile_script_UE + ' 2>&1 ; ' + task_UE

    logfile_compile_EPC = logdir_EPC + '/EPC_compile' + '_' + str(run) + '_.log'
    logfile_compile_HSS = logdir_EPC + '/HSS_compile' + '_' + str(run) + '_.log'
    logfile_exec_EPC = logdir_EPC + '/EPC_exec' + '_' + str(run) + '_.log'
    logfile_pre_exec_EPC = logdir_EPC + '/EPC_pre_exec' + '_' + str(run) + '_.log'
    logfile_exec_HSS = logdir_EPC + '/HSS_exec' + '_' + str(run) + '_.log'
    logfile_traffic_EPC = logdir_EPC + '/EPC_traffic' + '_' + str(run) + '_.log'
    logfile_task_EPC_out = logdir_EPC + '/EPC_task_out' + '_' + str(run) + '_.log'
    logfile_task_EPC = logdir_local_testcase + '/EPC_task' + '_' + str(run) + '_.log'
    task_EPC = ' ( \n'
    task_EPC = task_EPC + 'array_exec_pid=()' + '\n'
    task_EPC = task_EPC + 'cd ' + logdirOpenaircnRepo + '\n'
    task_EPC = task_EPC + update_config_file(oai_EPC, EPC_config_file, logdirOpenaircnRepo, logdirOpenaircnRepo+'/TEST/autotests/tools/search_repl.py') + '\n'
    task_EPC = task_EPC +  'source BUILD/TOOLS/build_helper \n'
    if EPC_compile_prog != "":
       task_EPC = task_EPC + '(' + EPC_compile_prog + ' ' + EPC_compile_prog_args +  ' ) > ' + logfile_compile_EPC + ' 2>&1 \n'
    if HSS_compile_prog != "":
       task_EPC = task_EPC + '(' + HSS_compile_prog + ' ' + HSS_compile_prog_args + ' ) > ' + logfile_compile_HSS + ' 2>&1 \n'
    if EPC_pre_exec != "":
       task_EPC  = task_EPC +  ' ( ' + EPC_pre_exec + ' '+ EPC_pre_exec_args + ' ) > ' + logfile_pre_exec_EPC + ' 2>&1 \n'
    if EPC_main_exec !=  "":
       task_EPC  = task_EPC + '(' + addsudo (EPC_main_exec + ' ' + EPC_main_exec_args, mypassword) + ' ) > ' + logfile_exec_EPC  +  ' 2>&1   & \n'
       task_EPC = task_EPC + 'array_exec_pid+=($!) \n'
       task_EPC = task_EPC + 'echo EPC_main_exec PID = $! \n'
    if HSS_main_exec !=  "":
       task_EPC  = task_EPC + '(' + addsudo (HSS_main_exec + ' ' + HSS_main_exec_args, mypassword) + ' ) > ' + logfile_exec_HSS  +  ' 2>&1   & \n'
       task_EPC = task_EPC + 'array_exec_pid+=($!) \n'
       task_EPC = task_EPC + 'echo HSS_main_exec PID = $! \n'
    if EPC_traffic_exec !=  "":
       task_EPC  = task_EPC + '(' + EPC_traffic_exec + ' ' + EPC_traffic_exec_args + ' ) > ' + logfile_traffic_EPC  +  ' 2>&1   & \n' 
       task_EPC = task_EPC + 'array_exec_pid+=($!) \n'  
       task_EPC = task_EPC + 'echo EPC_traffic_exec PID = $! \n'
    #terminate the EPC test case after timeout_cmd seconds   
    task_EPC = task_EPC + finalize_deploy_script (timeout_cmd, EPC_terminate_missing_procs) + '\n'
    #task_EPC  = task_EPC + 'sleep ' +  str(timeout_cmd) + '\n'
    task_EPC  = task_EPC + 'handle_ctrl_c' '\n' 
    task_EPC  = task_EPC + ' ) > ' + logfile_task_EPC_out + ' 2>&1 ' 
    write_file(logfile_task_EPC, task_EPC, mode="w")
    
    thread_EPC = oaiThread(1, "EPC_thread", oai_EPC , task_EPC, False, timeout_thread)
    thread_eNB = oaiThread(2, "eNB_thread", oai_eNB , task_eNB, False, timeout_thread)
    thread_UE = oaiThread(3, "UE_thread", oai_UE , task_UE, False, timeout_thread) 

    threads=[]
    threads.append(thread_eNB)
    threads.append(thread_UE)
    threads.append(thread_EPC)
    # Start new Threads

    thread_eNB.start()
    thread_UE.start()
    thread_EPC.start()

    #Wait for all the compile threads to complete
    for t in threads:
       t.join()
    #Now we get the log files from remote machines on the local machine

    cleanOldPrograms(oai_eNB, oldprogramList, CleanUpAluLteBox)
    cleanOldPrograms(oai_UE, oldprogramList, CleanUpAluLteBox)
    cleanOldPrograms(oai_EPC, oldprogramList, CleanUpAluLteBox)

    localfile = logdir_local_testcase + '/eNB_compile' + '_' + str(run) + '_.log'
    remotefile = logdir_eNB + '/eNB_compile' + '_' + str(run) + '_.log'
    sftp_log = os.path.expandvars(logdir_local_testcase + '/sftp_module.log')
    ports = 22
    sftp_module (user, password, eNBMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/eNB_exec' + '_' + str(run) + '_.log'
    remotefile = logdir_eNB + '/eNB_exec' + '_' + str(run) + '_.log'
    sftp_module (user, password, eNBMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/eNB_pre_exec' + '_' + str(run) + '_.log'
    remotefile = logdir_eNB + '/eNB_pre_exec' + '_' + str(run) + '_.log'
    sftp_module (user, password, eNBMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/eNB_traffic' + '_' + str(run) + '_.log'
    remotefile = logdir_eNB + '/eNB_traffic' + '_' + str(run) + '_.log'
    sftp_module (user, password, eNBMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/eNB_task_out' + '_' + str(run) + '_.log'
    remotefile = logdir_eNB + '/eNB_task_out' + '_' + str(run) + '_.log'
    sftp_module (user, password, eNBMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/UE_compile' + '_' + str(run) + '_.log'
    remotefile = logdir_UE + '/UE_compile' + '_' + str(run) + '_.log'
    sftp_module (user, password, UEMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/UE_exec' + '_' + str(run) + '_.log'
    remotefile = logdir_UE + '/UE_exec' + '_' + str(run) + '_.log'
    sftp_module (user, password, UEMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/UE_pre_exec' + '_' + str(run) + '_.log'
    remotefile = logdir_UE + '/UE_pre_exec' + '_' + str(run) + '_.log'
    sftp_module (user, password, UEMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/UE_traffic' + '_' + str(run) + '_.log'
    remotefile = logdir_UE + '/UE_traffic' + '_' + str(run) + '_.log'
    sftp_module (user, password, UEMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/UE_task_out' + '_' + str(run) + '_.log'
    remotefile = logdir_UE + '/UE_task_out' + '_' + str(run) + '_.log'
    sftp_module (user, password, UEMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/EPC_compile' + '_' + str(run) + '_.log'
    remotefile = logdir_EPC + '/EPC_compile' + '_' + str(run) + '_.log'
    sftp_module (user, password, EPCMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/EPC_exec' + '_' + str(run) + '_.log'
    remotefile = logdir_EPC + '/EPC_exec' + '_' + str(run) + '_.log'
    sftp_module (user, password, EPCMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/HSS_compile' + '_' + str(run) + '_.log'
    remotefile = logdir_EPC + '/HSS_compile' + '_' + str(run) + '_.log'
    sftp_module (user, password, EPCMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/HSS_exec' + '_' + str(run) + '_.log'
    remotefile = logdir_EPC + '/HSS_exec' + '_' + str(run) + '_.log'
    sftp_module (user, password, EPCMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/EPC_pre_exec' + '_' + str(run) + '_.log'
    remotefile = logdir_EPC + '/EPC_pre_exec' + '_' + str(run) + '_.log'
    sftp_module (user, password, EPCMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/EPC_traffic' + '_' + str(run) + '_.log'
    remotefile = logdir_EPC + '/EPC_traffic' + '_' + str(run) + '_.log'
    sftp_module (user, password, EPCMachine, ports, localfile, remotefile, sftp_log, "get")

    localfile = logdir_local_testcase + '/EPC_task_out' + '_' + str(run) + '_.log'
    remotefile = logdir_EPC + '/EPC_task_out' + '_' + str(run) + '_.log'
    sftp_module (user, password, EPCMachine, ports, localfile, remotefile, sftp_log, "get")
    #We need to close the new ssh session that was created  
    if index_eNBMachine == index_EPCMachine:
        oai_EPC.disconnect()


#thread1 = myThread(1, "Thread-1", 1)
debug = 0
pw =''
i = 0
dlsim=0
localshell=0
is_compiled = 0
timeout=2000
xmlInputFile="./test_case_list.xml"
NFSResultsDir = '/mnt/sradio'
cleanupOldProgramsScript = '$OPENAIR_DIR/cmake_targets/autotests/tools/remove_old_programs.bash'

logdir = '/tmp/' + 'OAITestFrameWork-' + getpass.getuser() + '/'
logdirOAI5GRepo = logdir + 'openairinterface5g/'
logdirOpenaircnRepo = logdir + 'openair-cn/'

openairdir_local = os.environ.get('OPENAIR_DIR')
if openairdir_local is None:
   print "Environment variable OPENAIR_DIR not set correctly"
   sys.exit()
locallogdir = openairdir_local + '/cmake_targets/autotests/log/'
#Remove  the contents of local log directory
os.system(' rm -fr ' + locallogdir + '; mkdir -p ' +  locallogdir  )

for arg in sys.argv:
    if arg == '-d':
        debug = 1
    elif arg == '-dd':
        debug = 2
    elif arg == '-p' :
        prompt2 = sys.argv[i+1]
    elif arg == '-w' :
        pw = sys.argv[i+1]
    elif arg == '-P' :
        dlsim = 1
    elif arg == '-l' :
        localshell = 1
    elif arg == '-c' :
        is_compiled = 1
    elif arg == '-t' :
        timeout = sys.argv[i+1]
    elif arg == '-h' :
        print "-d:  low debug level"
        print "-dd: high debug level"
        print "-p:  set the prompt"
        print "-w:  set the password for ssh to localhost"
        print "-l:  use local shell instead of ssh connection"
        print "-t:  set the time out in second for commands"
        sys.exit()
    i= i + 1     

try:  
   os.environ["OPENAIR1_DIR"]
except KeyError: 
   print "Please set the environment variable OPENAIR1_DIR in the .bashrc"
   sys.exit(1)

try:  
   os.environ["OPENAIR2_DIR"]
except KeyError: 
   print "Please set the environment variable OPENAIR2_DIR in the .bashrc"
   sys.exit(1)

try:  
   os.environ["OPENAIR_TARGETS"]
except KeyError: 
   print "Please set the environment variable OPENAIR_TARGETS in the .bashrc"
   sys.exit(1)

# get the oai object
host = os.uname()[1]
#oai = openair('localdomain','calisson')
oai_list = {}


#start_time = time.time()  # datetime.datetime.now()
user = getpass.getuser()
print "host = " + host 
print "user = " + user
pw=getpass.getpass()

#Now we parse the xml file for basic configuration
xmlTree = ET.parse(xmlInputFile)
xmlRoot = xmlTree.getroot()




MachineList = xmlRoot.findtext('MachineList',default='')
NFSResultsShare = xmlRoot.findtext('NFSResultsShare',default='')
GitOpenaircnRepo = xmlRoot.findtext('GitOpenair-cnRepo',default='')
GitOAI5GRepo = xmlRoot.findtext('GitOAI5GRepo',default='')
GitOAI5GRepoBranch = xmlRoot.findtext('GitOAI5GRepoBranch',default='')
GitOpenaircnRepoBranch = xmlRoot.findtext('GitOpenair-cnRepoBranch',default='')
CleanUpOldProgs = xmlRoot.findtext('CleanUpOldProgs',default='')
CleanUpAluLteBox = xmlRoot.findtext('CleanUpAluLteBox',default='')

print "MachineList = " + MachineList
print "GitOpenair-cnRepo = " + GitOpenaircnRepo
print "GitOAI5GRepo = " + GitOAI5GRepo
print "GitOAI5GBranch = " + GitOAI5GRepoBranch
print "GitOpenaircnRepoBranch = " + GitOpenaircnRepoBranch
print "NFSResultsShare = " + NFSResultsShare
cmd = "git show-ref --heads -s "+ GitOAI5GRepoBranch
GitOAI5GHeadVersion = subprocess.check_output ([cmd], shell=True)
print "GitOAI5GHeadVersion = " + GitOAI5GHeadVersion
print "CleanUpOldProgs = " + CleanUpOldProgs


MachineList = MachineList.split()

index=0
for machine in MachineList: 
  oai_list[index] = openair('localdomain',machine)
  index = index + 1


#myThread (1,"sddsf", 1)


#thread1 = oaiThread1(1, "Thread-1", 1)
#def __init__(self, threadID, name, counter, oai, cmd, sudo, timeout):

#sys.exit()







print "\nTesting the sanity of machines used for testing..."
if localshell == 0:
    try:
        index=0
        for machine in MachineList:
           print '\n******* Note that the user <'+user+'> should be a sudoer *******\n'
           print '******* Connecting to the machine <'+machine+'> to perform the test *******\n'
           if not pw :
              print "username: " + user 
              #pw = getpass.getpass() 
              #print "password: " + pw            
           else :
              print "username: " + user 
              #print "password: " + pw 
           # issues in ubuntu 12.04
           oai_list[index].connect(user,pw)
           #print "result = " + result
           

           #print '\nCleaning Older running programs : ' + CleanUpOldProgs
           #cleanOldPrograms(oai_list[index], CleanUpOldProgs)



           print '\nChecking for sudo permissions on machine <'+machine+'>...'
           result = oai_list[index].send_expect_false('sudo -S -v','may not run sudo',True)
           print "Sudo permissions..." + result
           
           print '\nCleaning Older running programs : ' + CleanUpOldProgs
           cleanOldPrograms(oai_list[index], CleanUpOldProgs, CleanUpAluLteBox)

           result = oai_list[index].send('mount ' + NFSResultsDir, True)
           print "Mounting NFS Share " + NFSResultsDir + "..." + result

           # Check if NFS share is mounted correctly.
           print 'Checking if NFS Share<' + NFSResultsDir + '> is mounted correctly...'
           #result = oai_list[index].send_expect('mount | grep ' + NFSResultsDir,  NFSResultsDir )
           cmd = 'if grep -qs '+NFSResultsDir+ ' /proc/mounts; then  echo \'' + NFSResultsDir  + ' is mounted\' ; fi'
           search_expr = NFSResultsDir + ' is mounted'
           print "cmd = " + cmd
           print "search_expr = " + search_expr
           result = oai_list[index].send_expect(cmd, search_expr)
           print "Mount NFS_Results_Dir..." + result
           index = index + 1
           
           #oai.connect2(user,pw) 
           #oai.get_shell()
    except :
        print 'Fail to connect to the machine: '+ machine 
        sys.exit(1)
else:
    pw = ''
    oai_list[0].connect_localshell()





cpu_freq = int(oai_list[0].cpu_freq())
if timeout == 2000 : 
    if cpu_freq <= 2000 : 
        timeout = 3000
    elif cpu_freq < 2700 :
        timeout = 2000 
    elif cpu_freq < 3300 :
        timeout = 1500
print "cpu freq(MHz): " + str(cpu_freq) + "timeout(s): " + str(timeout)

# The log files are stored in branch/version/



#result = oai_list[0].send('uname -a ' )
#print result

#We now prepare the machines for testing
#index=0
for index in oai_list:
  try:
      print "setting up machine: " + MachineList[index]
      #print oai_list[oai].send_recv('echo \''+pw+'\' |sudo -S -v')
      #print oai_list[oai].send_recv('sudo su')
      #print oai_list[oai].send_recv('who am i') 
      #cleanUpPrograms(oai_list[oai]
      cmd =  'mkdir -p ' + logdir + ' ; rm -fr ' + logdir + '/*'
      result = oai_list[index].send_recv(cmd)
     
      setuplogfile  = logdir  + '/setup_log_' + MachineList[index] + '_.txt'
      setup_script  = locallogdir  + '/setup_script_' + MachineList[index] +  '_.txt'
      cmd = ' ( \n'
      #cmd = cmd  + 'rm -fR ' +  logdir + '\n'
      #cmd = cmd + 'mkdir -p ' + logdir + '\n'
      cmd = cmd + 'cd '+ logdir   + '\n'
      cmd = cmd + 'git clone '+ GitOAI5GRepo  + '\n'
      cmd = cmd + 'git clone '+ GitOpenaircnRepo   + '\n'
      cmd = cmd +  'cd ' + logdirOAI5GRepo  + '\n'
      cmd = cmd + 'git checkout ' + GitOAI5GHeadVersion   + '\n'
      cmd = cmd + 'source oaienv'   + '\n'
      cmd = cmd +  'cd ' + logdirOpenaircnRepo  + '\n'
      cmd = cmd +  'git checkout ' + GitOpenaircnRepoBranch  + '\n'
      cmd = cmd +  'env |grep OPENAIR'  + '\n'
      cmd = cmd + ' cd ' + logdir   + '\n'
      cmd = cmd + ' ) > ' +  setuplogfile + ' 2>&1   '
      #cmd = cmd + 'echo \' ' + cmd  + '\' > ' + setup_script + ' 2>&1 \n '
      result = oai_list[index].send_recv(cmd, False, 300 )
      write_file(setup_script, cmd, mode="w")
      localfile = locallogdir + '/setup_log_' + MachineList[index] + '_.txt'
      remotefile = logdir  + '/setup_log_' + MachineList[index] + '_.txt'

      sftp_log = os.path.expandvars(locallogdir + '/sftp_module.log')
      sftp_module (user, pw, MachineList[index], 22, localfile, remotefile, sftp_log, "get")


      #Now we copy test_case_list.xml on the remote machines
      localfile = os.path.expandvars('$OPENAIR_DIR/cmake_targets/autotests/test_case_list.xml')
      remotefile = logdirOAI5GRepo + '/cmake_targets/autotests/test_case_list.xml'

      sftp_log = os.path.expandvars(locallogdir + '/sftp_module.log')
      sftp_module (user, pw, MachineList[index], 22, localfile, remotefile, sftp_log, "put")


      #print oai_list[index].send('rm -fR ' +  logdir)
      #print oai_list[index].send('mkdir -p ' + logdir)
      #print oai_list[index].send('cd '+ logdir)
      #print oai_list[index].send('git clone '+ GitOAI5GRepo )
      #print oai_list[index].send('git clone '+ GitOpenaircnRepo)
      #print oai_list[index].send('cd ' + logdirOAI5GRepo)
      #print oai_list[index].send('git checkout ' + GitOAI5GHeadVersion)
      #print oai_list[index].send('source oaienv')
      #print oai_list[index].send('cd ' + logdirOpenaircnRepo)
      #print oai_list[index].send('git checkout ' + GitOpenaircnRepoBranch)
      #print oai_list[index].send_recv('cd ' + logdirOAI5GRepo)
      #print oai_list[index].send_recv('source oaienv')
      #print oai_list[index].send_recv('env |grep OPENAIR')

      #print '\nCleaning Older running programs : ' + CleanUpOldProgs
      #cleanOldPrograms(oai_list[index], CleanUpOldProgs)

  except :
      print 'There is error in one of the commands to setup the machine '+ MachineList[index] 
      sys.exit(1)


#Now we process all the test cases


testcaseList=xmlRoot.findall('testCase')
#print testcaseList
for testcase in testcaseList:
   testcasename = testcase.get('id')
   testcaseclass = testcase.findtext('class',default='')
   desc = testcase.findtext('desc',default='')
   if testcaseclass == 'lte-softmodem' :
     if testcasename != '015700':
     	continue
     eNBMachine = testcase.findtext('eNB',default='')
     UEMachine = testcase.findtext('UE',default='')
     EPCMachine = testcase.findtext('EPC',default='')
     index_eNBMachine = MachineList.index(eNBMachine)
     index_UEMachine = MachineList.index(UEMachine)
     index_EPCMachine = MachineList.index(EPCMachine)
     print "testcasename = " + testcasename + " class = " + testcaseclass
     handle_testcaseclass_softmodem (testcase, CleanUpOldProgs, oai_list, logdirOAI5GRepo, logdirOpenaircnRepo, MachineList, pw, CleanUpAluLteBox )

   elif testcaseclass == 'compilation' :
     continue
     handle_testcaseclass_compilation (testcase)
   elif testcaseclass == 'execution' :
     continue
     handle_testcaseclass_oaisim (testcase)
   else :
     print "Unknown test case class: " + testcaseclass
     sys.exit()


sys.exit()


   #+ "class = "+ classx



      #index = index +1

test = 'test01'
ctime=datetime.datetime.utcnow().strftime("%Y-%m-%d.%Hh%M")
logfile = user+'.'+test+'.'+ctime+'.txt'  
logdir = os.getcwd() + '/pre-ci-logs-'+host;
oai.create_dir(logdir,debug)    
print 'log dir: ' + logdir
print 'log file: ' + logfile
pwd = oai.send_recv('pwd') 
print "pwd = " + pwd
result = oai.send('echo linux | sudo -S ls -al;sleep 5')
print "result =" + result
sys.exit()

#oai.send_nowait('mkdir -p -m 755' + logdir + ';')

#print '=================start the ' + test + ' at ' + ctime + '=================\n'
#print 'Results will be reported in log file : ' + logfile
log.writefile(logfile,'====================start'+test+' at ' + ctime + '=======================\n')
log.set_debug_level(debug)

oai.kill(user, pw)   
oai.rm_driver(oai,user,pw)

# start te test cases 
if is_compiled == 0 :
    is_compiled=case01.execute(oai, user, pw, host,logfile,logdir,debug,timeout)
    
if is_compiled != 0 :
    case02.execute(oai, user, pw, host, logfile,logdir,debug)
    case03.execute(oai, user, pw, host, logfile,logdir,debug)
    case04.execute(oai, user, pw, host, logfile,logdir,debug)
    case05.execute(oai, user, pw, host, logfile,logdir,debug)
else :
    print 'Compilation error: skip test case 02,03,04,05'

oai.kill(user, pw) 
oai.rm_driver(oai,user,pw)

# perform the stats
log.statistics(logfile)


oai.disconnect()

ctime=datetime.datetime.utcnow().strftime("%Y-%m-%d_%Hh%M")
log.writefile(logfile,'====================end the '+ test + ' at ' + ctime +'====================')
print 'Test results can be found in : ' + logfile 
#print '\nThis test took %f minutes\n' % math.ceil((time.time() - start_time)/60) 

#print '\n=====================end the '+ test + ' at ' + ctime + '====================='
