#!/usr/bin/python3
#                   RBLandau 20210509
#
'''
CheckNet3.py

Check the state of the network.
Ping some nodes, translate some names, retrieve some pages. arg: 
Record a marker at the beginning of each checking cycle.  
Record only errors.
One CLI arg: either logfilename or "-" for stdout.  If aimed at a file, 
THE LOG FILE MUST EXIST, perhaps empty, when the program starts!
If the log file is not NTRC.ntrace-accessible, complain.  Check this on
 every attempt to write anything to the file.  Complain and
 retry with exponential backoff.  

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
import requests
import datetime
#import TKinter
from NewTrace   import NTRC, ntrace, ntracef


# c l a s s   C G  
# Read-only or write-once global data.
class CG():
    
    # PING    
    lNodesPing = [ "smtp.ricksoft.com", "mail.ricksoft.com" 
                    , "www.yahoo.com"  
                    , "www.bing.com" 
#                    , "wxyz.thisisabadname.foo"
                    ]

    # TRANSLATE NAMES
    lNodesXlate = [ "www.ricksoft.com", "mail.ricksoft.com" 
                    , "www.yahoo.com", "www.cnn.com" 
                    , "www.ebay.com", "www.half.com" 
#                    , "wxyz.thisisabadname.foo"
                    ]

    lNodesUrls = [ "http://www.google.com"
                    , "http://www.bing.com" 
                    , "http://www.ricksoft.com"
#                    , "http://www.ricksoft.com/thisisabadname"
                    ]

    # Default log file and repeat cycle.
    nRepeatInterval_Default = 15
    nRepeatInterval = int(nRepeatInterval_Default)  # for production
    sLogFile_Default = "./ChkNetPy3.log"
    sLogFile = sLogFile_Default

    cLog = None         # instance ptr for everyone to use


# c l a s s   C L o g 
class CLog(object):
    '''
    Write to an existing log file, or maybe stdout.

    Test that the log file is available before writing;
    complain if not.  Retry with exponential backoff.
    '''

    nInitialRetryInterval = 1       # timeout in minutes
    nRetriesBeforeSlow = 10         # 
    bFound = False

    
    @ntracef("LOG")
    def __init__(self, myFilename="stdout"):
        self.sLogFile = myFilename


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
        if self.sLogFile == "stdout":
            print(sOut)
            idxErrorCount = 0
        else:
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
        NTRC.ntracef(3, "LOG", f"proc done {sOut!r} {idxErrorCount=}")


    @ntracef("LOG", level=5)
    def fsTimestamp(self):
        return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


    @ntracef("LOG")
    def testFile(self, myFile, myTimeout, myRetries):
        '''
        testFile: Test that file exists, complain if not.
        '''
        
        if myFile == "stdout": return True
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


# c l a s s   C C o m m a n d
class CCommand(object):
    '''
    Execute a CLI command, parse results
     using a regular expression supplied by the caller.  
    '''

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


# c l a s s   C P i n g 
class CPing(CCommand):
    '''
    Ping a series of nodes.
    List of nodes supplied by caller.  
    
    Retry count supplied by caller.  
    Inherits capabilities from CCommand.
    '''

    @ntracef("PING")
    def __init__(self, mylNodes, mynTimes=1):
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
            self.sOsCommand = (
                        "/usr/bin/ping --count=%s --size=64 %s 2>/dev/null" 
                        % (self.nTimes, "%s"))
            self.sOsRegex = "(\d+) packets received"
        NTRC.ntracef(2,"PING","exit  CPing cmd|%s| regex|%s|"
                % (self.sOsCommand, self.sOsRegex))
# Quiet today
#        g.cLog.fWriteLine("Pinging %s nodes" % (len(self.lNodes)))
        

    @ntracef("PING")
    def execute(self):
        for sNode in self.lNodes:
            sCommand = self.sOsCommand % (sNode)
            NTRC.ntracef(3, "PING", "proc CPing.execute cmd|%s| regex|%s|" 
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
            sResult = "Ping %-38s %s" % (sNode, sEval)
            if not sEval == "ok":
                g.cLog.fWriteLine("Ping! %s" % (sResult))


# c l a s s   C X l a t e 
class CXlate(CCommand):
    '''
    DNS-translate a series of domain names.
    List of nodes supplied by caller.  
    
    Weirdness: RoadRunner in Austin does not ever fail to 
     translate a name; it always redirects to an RR page.
     A bad name will still translate to something.  
     The only possible failure is that the DNS server cannot
     be reached at all.  Report those.  
    
    Repaired 20210508: use socket.gethostbyname instead, 
     which appears to work well on Xfinity internet. 

    Inherits capabilities from CCommand.
    '''
    

    @ntracef("XLAT") 
    def __init__(self, mylNodes):
        self.lNodes = mylNodes
        

    @ntracef("XLAT")
    def getIP(self, sDomainName):
        """
        Find an IP addr for a domain name.
        Return addr as string or return None.  
        """
        try:
            data = socket.gethostbyname(sDomainName)
            ip = repr(data)
            return ip
        except Exception:
            # fail gracefully
            return None


    @ntracef("XLAT")
    def execute(self):
        for sNode in self.lNodes:
            sIpAddr = self.getIP(sNode)
            NTRC.ntracef(3, "XLAT", f"proc {sNode} translates to {sIpAddr}")
            if sIpAddr:
                sEval = "ok"
            else:
                sEval = "notrans"
                sResult = "Xlate %-36s %s" % (sNode, sEval)
                if not sEval == "ok":
                    g.cLog.fWriteLine("Xlate! %s" % (sResult))


# c l a s s   C G e t H t t p 
class CGetHttp(CCommand):
    '''
    Retrieve a series of HTTP pages.
    Inherits capabilities from CCommand.
    '''

    @ntracef("HTTP")
    def __init__(self, mylNodes):
        self.lNodes = mylNodes


    @ntracef("HTTP")
    def execute(self):
        pass
        for sUrl in g.lNodesUrls:
            response = requests.get(sUrl)
            result = response.status_code
            NTRC.ntracef(3, "HTTP", f"proc {sUrl} get status {result}")
            if result == 200:
                sEval = "ok"
            elif result == 404:
                sEval = "notfound"
            else:
                sEval = "fail"
            sResult = "HTTP %-32s %s" % (sUrl, sEval)
            if not sEval == "ok":
                g.cLog.fWriteLine("HTTP! %s" % (sResult))


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
# 20210509  RBL Redo a lot.  
#               Fill out code for CXlate and CGetHttp.
# 
# 

#END
