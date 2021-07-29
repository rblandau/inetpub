# inetpub

## CheckNetPy project to monitor network: is it up and running?
This program has been running in one form or another since 1994.  It was originally developed as a very, very cheap alternative to fancy network monitoring software, because our operations group did not monitor closely the health of our worldwide network, though many of the engineering and manufacturing groups depended on 24/7 network access all over the U.S., Europe, and Asia.  

The original incarnation was a shell script running on some form of UNIX, probably ULTRIX.  Then better shell, then Perl, then better Perl.  And eventually Python, and now half-decent Python3.  This new Python3 version is fully fleshed out and reasonably reliable.  

Runs on Cygwin/Windows10 and on Ubuntu (Raspbian for Rasberry Pi).  Pretty sure it will also run on straight Windows10.  Note that it requires the requests library to be installed on Python3.  

Intended application: use cron or similar to schedule this to run regularly.
The program executes once and exits.  My current version runs, thanks to cron, every ten minutes to sniff the network health.  

Requires an existing (and accessible) log file.  
The program records that it is beginning, with date and time stamp of the form 
YYYYMMDD_HHMMSS.  Any errors encountered are also logged, conspicuously and with relevant information. A little sample output:

    20210728_234844   CheckNet CheckNetPy4_01.py checking network from RICKS-YOGA940 ******
    20210728_234942   CheckNet CheckNetPy4_01.py checking network from RICKS-YOGA940 ******
    20210728_235329   CheckNet CheckNetPy4_01.py checking network from RICKS-YOGA940 ******
    20210728_235330   Ping!  Ping  192.168.1.1                                  fail
    20210728_235330   Ping!  Ping  smtp.ricksoft.com                            fail
    20210728_235330   Ping!  Ping  mail.ricksoft.com                            fail
    20210728_235330   Ping!  Ping  www.yahoo.com                                fail
    20210728_235330   Ping!  Ping  www.bing.com                                 fail
    20210729_001352   CheckNet CheckNetPy4_01.py checking network from RICKS-YOGA940 ******

The program pings a few nodes, DNS-translates a few names, and finally accesses a few web pages.  Feel free to change the lists of sites, names, and pages to be used to meet current needs and personal preferences.  

One CLI argument: log filename (relative to current directory).  The file must already exist and be accessible to the program, which will append its output to the file.  If no filename is given, the default is "./ChkNetPy4.log" .
For testing use, the filename argument can be "-" (just the minus sign, not the quotation marks), which will force output to stdout rather than to the log file.  

Happy networking!

