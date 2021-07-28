#!/usr/bin/python3
#                   RBLandau 20200309
#
'''
CheckNet3.py

Check the state of the network.
Ping some nodes, translate some names, retrieve some pages.
Record a marker at the beginning of each checking cycle.  
Record only errors.
THE LOG FILE MUST EXIST, perhaps empty, when the program starts!
If the log file is not NTRC.ntrace-accessible, complain.  Check this on
 every attempt to write anything to the file.  Complain and
 retry with exponential backoff.  

Run one time and exit!
Unlike the old versions, this will run once and exit.  
 A cron job or equivalent will run this every so often.

One optional CLI arg: filespec for log file.  Defaults to current directory,
 ./chknetpy3.log

New version for python3 20200309.

@author: landau
'''

import sys
import os
import time
import re
import socket
#import requests
import datetime
#import TKinter
from NewTraceFac   import NTRC, ntrace, ntracef


# ----------------------------------------------
# class CG 
# Read-only or write-once global stuff.
class CG():
    
    # PING    
    lNodesPing = [ "192.168.1.1"
                 , "smtp.ricksoft.com", "mail.ricksoft.com" 
                 , "www.yahoo.com"  
                 , "www.bing.com" 
                 ]

    # TRANSLATE NAMES
    lNodesXlate = [ "www.ricksoft.com", "mail.ricksoft.com" \
                  , "www.yahoo.com", "www.cnn.com" \
                  , "www.ebay.com", "www.half.com" \
                  ]

    lNodesUrls = [ "http://www.google.com", "http://www.bing.com" ]

    # Default log file and repeat cycle.
    nRepeatInterval_Default = 15
    nRepeatInterval = int(nRepeatInterval_Default)  # for production
    sLogFile_Default = "./ChkNetPy3.log"
    sLogFile = sLogFile_Default

    cLog = None         # instance ptr for everyone to use


# ----------------------------------------------
# class  C L o g 
class CLog(object):
    '''
    class CLog: Write to a log file.

    Test that the log file is available before writing;
    complain if not.  Retry with exponential backoff.
    '''

    nInitialRetryInterval = 1       # timeout in minutes
    nRetriesBeforeSlow = 10         # 
    bFound = False

    
    @ntracef("LOG")
    def __init__(self, myFilename):
        if myFilename: self.sLogFile = myFilename


    @ntracef("LOG")
    def fWriteLine(self, mysLine):
        '''
        function fWriteLine: If the file is available, scribble into it.
        '''
        # Get a timestamp
        ascT = self.fsTimestamp()
        sOut = "%s   %s" % (ascT, mysLine)
        
        # Check that the file is accessible before we try to write into it.
        self.testFile(self.sLogFile, self.nInitialRetryInterval, 0)
        # That should have been sufficient, but sometimes it's not and
        #  the file shows up as busy.  Retry a few times.  
        for idxErrorCount in range(5+1):    # five retries
            NTRC.ntracef(3, "LOG", ("proc writeline line|%s| errs|%s|" 
                        % (mysLine, idxErrorCount)))
            try:
                with open(self.sLogFile, "a") as fhOut:
                    if idxErrorCount == 0:
                        fhOut.write(sOut+"\n")
                    else:
                        fhOut.write((sOut+" ioretries|%s|" 
                                    % (idxErrorCount))+"\n")
                    fhOut.flush()
                break
            except IOError:
                NTRC.ntrace(3, 
                    "ERROR fWriteLine IOError try|%s| file|%s| line|%s|" 
                    % (idxErrorCount+1, self.sLogFile, sOut))
                sleep(1)
        #print sOut             # for debugging


    @ntracef("LOG", level=5)
    def fsTimestamp(self):
#        vecT = time.localtime()
#        (yr, mo, da, hr, min, sec) = vecT[0:6]
#        ascT = "%4d%02d%02d_%02d%02d%02d" % (yr, mo, da, hr, min, sec)
#        return ascT
        return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    @ntracef("LOG")
    def testFile(self,myFile, myTimeout, myRetries):
        '''
        function testFile: Test that file exists, complain if not.
        '''
        
        # TEMP TEMP TEMP TEMP TEMP TEMP 
        if self.bFound: return True
        # END TEMP END TEMP END TEMP
        sTime = self.fsTimestamp()
        try:
            with open(self.sLogFile, "a") as fhOut:
                if not self.bFound:
                    NTRC.ntracef(1, "LOG", ("%s Found log file |%s|" 
                                % (sTime, myFile)))
                self.bFound = True
        except (ValueError, IOError):
            self.bFound = False
            print("%s Error: Unable to open log file |%s|" 
                    % (sTime, myFile))
            for i in range(myTimeout):
                self.BeepMe()
            time.sleep(myTimeout)
            # Slow exponential backoff.  Exhaust a bunch of retries and then
            # slow down the retry interval.  
            # Limit the backoff to about four minutes.  
            if myRetries >= self.nRetriesBeforeSlow:
                if myTimeout < 200: myTimeout *= 2
                self.testFile(myFile, myTimeout,0)
            else:
                self.testFile(myFile, myTimeout, myRetries+1)


    @ntracef("LOG")
    def BeepMe(self):
        # TEMP TEMP TEMP until we figure out why this stopped working.
        return
        # END TEMP
        window = Tkinter.Tk()
        window.bell()
        window.destroy()


# ----------------------------------------------
# class  C C o m m a n d
class CCommand(object):
    '''
    class CCommand: Execute a CLI command, parse results
    using a regular expression supplied by the caller.  
    '''
    ID = 99


    @ntracef("CMD")
    def doCmd(self, mysCommand):
        sResult = ""
        for sLine in os.popen(mysCommand):
            sResult += sLine.strip()
        return sResult
        

    @ntracef("CMD")
    def doParse(self, mysCommand, mysRegex):
        sOutput = self.doCmd(mysCommand)
        mCheck = re.search(mysRegex, sOutput)
        if mCheck:
            sResult = mCheck.groups()
        else:
            sResult = None
        return sResult


# ----------------------------------------------
# class  C P i n g 
class CPing(CCommand):
    '''
    class CPing: Ping a series of nodes.
    List of nodes supplied by caller.  
    Retry count supplied by caller.  
    '''


    @ntracef("PING")
    def __init__(self, mylNodes, mynTimes=1):
        self.ID = 99
        self.lNodes = mylNodes
        self.nTimes = mynTimes
        # Determine whether it is Windows ping or Cygwin ping
        # and set the command and regex appropriately.  
        # The ping command with a --help option gives some, and, fortunately, 
        # the two systems are detectably different.  
        lTmp = self.doParse("ping --help", "(gnu.org)")
        if not lTmp:
            self.sOsCommand = ("/cygdrive/c/WINDOWS/system32/ping -n %s %s"
                    % (self.nTimes,"%s"))
            self.sOsRegex = "Received = (\d+)"
        else:
            self.sOsCommand = ("/usr/bin/ping --count=%s --size=64 %s" 
                    % (self.nTimes, "%s"))
            self.sOsRegex = "(\d+) packets received"
        NTRC.ntracef(2,"PING","exit  CPing cmd|%s| regex|%s|"
                % (self.sOsCommand, self.sOsRegex))
# Quiet today
#        g.cLog.fWriteLine("Pinging %s nodes" % (len(self.lNodes)))
        

    @ntracef("PING")
    def execute(self):
        for sNode in self.lNodes:
            sResult = self.pingone(sNode)
        return


    @ntracef("PING")
    def pingone(self, mysNode):
        sCommand = self.sOsCommand % (mysNode)
        NTRC.ntracef(3, "PING", "proc CPing.pingone cmd|%s| regex|%s|" 
                % (sCommand, self.sOsRegex))
        lOutput = self.doParse(sCommand, self.sOsRegex)
        if lOutput:
            try:
                nOk = int(lOutput[0])
            except (ValueError, TypeError):
                nOk = 0
            if nOk == 0:
                sEval = "notok"
            else:
                sEval = "ok"
        else:
            sEval = "fail"
        sResult = "Ping %-32s %s" % (mysNode, sEval)
        if not sEval == "ok":
            g.cLog.fWriteLine("Ping! %s" % (sResult))
        return (sEval, sResult)
    

# ----------------------------------------------
# class  C X l a t e 
class CXlate(CCommand):
    '''
    class CXlate: DNS-translate a series of domain names.
    List of nodes supplied by caller.  
    
    Weirdness: RoadRunner in Austin does not ever fail to 
    translate a name; it always redirects to an RR page.
    A bad name will still translate to something.  
    The only possible failure is that the DNS server cannot
    be reached at all.  Report those.  
    '''
    

    @ntracef("XLAT")
    def __init__(self, mylNodes):
        self.lNodes = mylNodes
        self.ID = 99
        

    @ntracef("XLAT")
    def execute(self):
        # TEMP TEMP TEMP until we figure out why this stopped working.
        NTRC.ntracef(2, "XLAT","exit CXlate.execute temporary quick exit ****************")
        return
        # END TEMP
        for sNode in self.lNodes:
            pass
            try:
                lNames = socket.gethostbyname_ex(sNode)
                lAlias = lNames[1]
            except:
                lNames = ["RBL:NetworkError"]
                lAlias = ["RBL:NetworkError"]
            NTRC.ntrace(5, "proc xlate node|%s| result|%s|"
                    % (sNode, lNames))
            sResult = "Xlate %s => %s" % (sNode, lAlias) 
            if len(lAlias) > 0 and lAlias[0] == "RBL:NetworkError":
                g.cLog.fWriteLine("Xlate! %s" % (sResult))
        # use socket.gethostbyname_ex(...)[1]
        pass



# ----------------------------------------------
# class  C G e t H t t p 
class CGetHttp(CCommand):
    '''
    class CGetHttp: retrieve a series of HTTP pages.
    '''


    @ntracef("HTTP")
    def __init__(self, mylNodes):
        self.lNodes = mylNodes
        self.ID = 99


    @ntracef("HTTP")
    def execute(self):
        pass


# ----------------------------------------------
# M A I N  L I N E 
@ntracef("MAIN")
def main(mysLogFile):
    # Start the log.  
    g.cLog = CLog(mysLogFile)
    # Log a line every time the utility is restarted.  
    # Make it conspicuous and easy to find in a long listing.  
    sHostname = socket.gethostname()
    sHeader = ("CheckNet %s checking network from %s ******" 
            % (sys.argv[0], sHostname))
    g.cLog.fWriteLine(sHeader)

    cPing = CPing(g.lNodesPing)
    cXlate = CXlate(g.lNodesXlate)
    cHttp = CGetHttp(g.lNodesUrls)

    cPing.execute()
    cXlate.execute()
    cHttp.execute()
    
    return(0)


# ----------------------------------------------
# E N T R Y   P O I N T 

if __name__ == '__main__':
    g = CG()

    '''
    One CLI arg: logfile name, optional.
    '''
    # Command line arguments override defaults
    # Output goes to default if $1 absent, to stdout if it is "-".
    t1 = None
    if len(sys.argv) > 1: t1 = sys.argv[1]
    if t1: 
        if t1 == "-":
            g.sLogFile = "stdout"
        else:
            g.sLogFile = t1
    else:
        g.sLogFile = g.sLogFile_Default

    sys.exit(main(g.sLogFile))

# end

# Edit history: 
# 1987xxxx  RBL First crude sh version running at DEC on ULTRIX.
# 1992xxxx  RBL Reliable sh version running at DEC on OSF/1, I think.
# 2002xxxx  RBL Enhanced Perl version, to monitor bloody flaky DSL.  
# 2007xxxx  RBL Original Python version for improved reliability.
# 20130830  RBL Enhanced argument handling.
#               Relocate log file to permanent, not network share, disk.
# 20130831  RBL Fix typo and default settings.  
# 20141030  RBL Temporarily disable beep and name translation, which
#                seem to fail reliably today.  Why?
#               Add retries for writing log file in case of file-busy
#                IOErrors, which appeared magically today.  
#                Also had to add this careful-writing retry technique
#                to the traditional NewTraceFac package, producing v10.
# 20141022  RBL Switch to new style tracef decorators.
#               Add explicit flush at end of log write.  
# 20170226  RBL Edit ping-list to eliminate permanent errors.  
#               Remove old, commented-out, redundant traces at function
#                entry and exit, replaced by decorators years ago.  
#               Someday, I'll have to add back name-translate and 
#                http access tests.  
# 20200309  RBL Redo and improve for python3.
#               Change from repeating to one-shot, so cron (or similar) 
#                has to run this at regulat intervals.  
#               Add option for writing to stdout, for testing.  
# 20200802  RBL Remove PING info output line.
#               Improve comments slightly.
# 20210727  RBL Add check, do we have local network at all.
# 
# 

#END
