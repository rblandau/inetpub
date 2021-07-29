#!/usr/bin/python3
#                   RBLandau 20210728
#
'''
CheckNet4.py

Check the state of the network.
 Ping some nodes, translate some names, retrieve some pages. arg: 
 Record a marker at the beginning of each checking cycle.  
 Record only errors.

One optional CLI arg: either logfilename or "-" for stdout.  
 Defaults to Defaults to current directory, ./ChkNetPy4.log
If aimed at a file, 
 THE LOG FILE MUST EXIST, perhaps empty, when the program starts!
If the log file is not NTRC.ntrace-accessible, complain.  Check this on
 every attempt to write anything to the file.  Complain and
 retry with exponential backoff.  

RUN ONE TIME AND EXIT!
 Unlike the old versions, this will run once and exit.  
 A cron job or equivalent will run this every so often.

New version for python3 20200309; and further improvements since then.

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


# ----------------------------------------------
# c l a s s   C G  
# Read-only or write-once global data.
class CG():
    
    # PING    
    lNodesPing = [ "192.168.1.1"
#                    , "www.ricksoft.com"
                    , "smtp.ricksoft.com", "mail.ricksoft.com" 
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
#    nRepeatInterval_Default = 15
#    nRepeatInterval = int(nRepeatInterval_Default)  # for production
    sLogFile_Default = "./ChkNetPy4.log"
    sLogFile = sLogFile_Default

    cLog = None         # instance ptr for everyone to use


# ----------------------------------------------
# c l a s s   C L o g 
class CLog(object):
    '''
    class CLog: Write to an existing log file, or maybe to stdout.

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
        NTRC.ntracef(3, "LOG", f"proc done {sOut!r} errs {idxErrorCount}")


    @ntracef("LOG", level=5)
    def fsTimestamp(self):
        return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


    @ntracef("LOG")
    def testFile(self, myFile, myTimeout, myRetries):
        '''
        function testFile: Test that file exists, complain if not.
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


# ----------------------------------------------
# c l a s s   C C o m m a n d
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
# c l a s s   C P i n g 
class CPing(CCommand):
    '''
    class CPing: Ping a series of nodes.
    List of nodes supplied by caller.  
    
    Retry count supplied by caller.  
    Inherits capabilities from CCommand.
    '''
    ID = 99
    
    
    @ntracef("PING")
    def __init__(self, mylNodes, mynTimes=1):
        self.lNodes = mylNodes
        self.nTimes = mynTimes
        
        # Determine whether it is Windows ping or Cygwin or Ubuntu
        #  and set the command and counter regex appropriately.  

        """
        Most pings come with a -V option for version, and the 
         results are detectably different.
        
        Windows 
        ping -V => "Bad option -V"
        Cygwin
        ping -V => "ping (GNU inetutils) 1.9.4"
        Ubuntu
        ping -V => "ping utility, iputils-s20180629"
        """

        # Empty until we determine the right type.    
        self.sPingType = ""
        (self.sOsCommand, self.sOsRegex) = ("", "")
        
        # Ubuntu:
        if not self.sPingType:
            lTmp = self.doParse("ping -V", "(ping utility)")
            if lTmp:
                self.sPingType = "Ubuntu"
                self.sOsCommand = ("ping -c %s %s"
                        % (self.nTimes,"%s"))
                self.sOsRegex = "(%d+) received"

        # Cygwin:
        if not self.sPingType:
            lTmp = self.doParse("ping -V", "(GNU inetutils)")
            if lTmp:
                self.sPingType = "Cygwin"
                self.sOsCommand = ("ping -c %s %s"
                        % (self.nTimes,"%s"))
                self.sOsRegex = "(\d+) packets received"

        # Windows:
        if not self.sPingType:
            lTmp = self.doParse("ping -V", "(Bad option)")
            if lTmp:
                self.sPingType = "Windows"
                self.sOsCommand = ("/cygdrive/c/WINDOWS/system32/ping -n %s %s"
                        % (self.nTimes,"%s"))
                self.sOsRegex = "Received = (\d+)"
        
        NTRC.ntracef(2,"PING","exit  CPing os|%s| cmd|%s| regex|%s|"
            % (self.sPingType, self.sOsCommand, self.sOsRegex))
        

    @ntracef("PING")
    def execute(self):
        # If we couldn't figure out what OS ping type to use, 
        #  don't do it at all.
        if self.sPingType:
            for sNode in self.lNodes:
                sResult = self.ping_one(sNode)
        return


    @ntracef("PING")
    def ping_one(self, mysNode):
        sCommand = self.sOsCommand % (mysNode)
        NTRC.ntracef(3, "PING", "proc CPing.ping_one cmd|%s| regex|%s|") 
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
        sResult = "Ping %-44s %s" % (mysNode, sEval)
        if not sEval == "ok":
            g.cLog.fWriteLine("Ping!  %s" % (sResult))
        return (sEval, sResult)


# ----------------------------------------------
# c l a s s   C X l a t e 
class CXlate(CCommand):
    '''
    class CXlate: DNS-translate a series of domain names.
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
    ID = 99
    

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
            result = self.xlat_one(sNode)
        return


    @ntracef("XLAT")
    def xlat_one(self, mysNode):
        sIpAddr = self.getIP(mysNode)
        NTRC.ntracef(3, "XLAT", f"proc {mysNode} translates to {sIpAddr}")
        if sIpAddr:
            sEval = "ok"
            sResult = "Xlat %-44s %s" % (mysNode, sEval)
        else:
            sEval = "notrans"
            sResult = "Xlat %-44s %s" % (mysNode, sEval)
            if not sEval == "ok":
                g.cLog.fWriteLine("Xlate! %s" % (sResult))
        return (sEval, mysNode, sResult)


# ----------------------------------------------
# c l a s s   C G e t H t t p 
class CGetHttp(CCommand):
    '''
    class CGetHttp: Retrieve a series of HTTP pages.
    Inherits capabilities from CCommand.
    '''
    ID = 99

    @ntracef("HTTP")
    def __init__(self, mylNodes):
        self.lNodes = mylNodes


    @ntracef("HTTP")
    def execute(self):
        for sUrl in g.lNodesUrls:
            result = self.gethttp_one(sUrl)
        return


    @ntracef("HTTP")
    def gethttp_one(self, mysUrl):
        response = requests.get(mysUrl)
        result = response.status_code
        NTRC.ntracef(3, "HTTP", f"proc {mysUrl} get status {result}")
        if result == 200:
            sEval = "ok"
        elif result == 404:
            sEval = "notfound"
        else:
            sEval = "fail"
        sResult = "HTTP %-44s %s" % (mysUrl, sEval)
        if not sEval == "ok":
            g.cLog.fWriteLine("HTTP!  %s" % (sResult))
        return (sEval, mysUrl, sResult)


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
# 20210509  RBL Redo a lot.  
#               Fill out code for CXlate and CGetHttp.
# 20210728  RBL Add check: do we have a local network at all?
#               Restructure CPing: take the logic out of the for loop.
#               Restructure CXlate and CGetHttp, too, the same way.
# 
# 

#END
