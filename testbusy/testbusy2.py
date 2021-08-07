#!/usr/bin/python
# Test program to demonstrate the file-busy problem.

# Write a whole bunch of lines appended to a 
from time import sleep,localtime
from NewTraceFac import TRC,trace,tracef

# This is the guy that fails.  This code is taken almost letter for letter
#  from the program that fails reliably.  (In the original, this is a class
#  method, but I don't think that should matter significantly.  
def fWriteCarefully(outfile, mode, outline, retries):
    # Careful: if the file is still busy with the last write, 
    #  wait a second and try it again.  A few times.
    #  Yes, this actually happens disturbingly frequently.
    for iErrorCount in range(retries+1):
        try:
            with open(outfile, mode) as fh:
                if iErrorCount == 0:
                    fh.write(outline + "\n")
                else:
                    outline += " filebusyretries|%s|"%(iErrorCount)
                    fh.write(outline + "\n")
                #fh.flush()           # Should be unnecessary but maybe improves timing.
                #fh.close()           # Should be unnecessary but maybe improves timing.
            break                   # Leaves the for loop.
        except IOError, e:
            sleep(1)
    # If we can't write after several retries, tough.  

def fnsTimestamp():
    # Get a timestamp
    (yr,mo,da,hrs,mins,secs,x,y,z) = localtime()
    ascT = "%4d%02d%02d_%02d%02d%02d" % (yr,mo,da,hrs,mins,secs)
    return ascT + " "

def fWriteOneGroup(idxGroup):
    for iLine in xrange(5):
        sLine = fnsTimestamp() + "group %7d line %2d 12345678901234567890123456789012345678901234567890123456789012345678901234567890" % (idxGroup,iLine)
        print sLine
        fWriteCarefully("testbusy1_out.log", 'a', sLine, 10)

def main():
    fWriteCarefully("testbusy1_out.log", 'a', "*** RESTARTING ***", 10)
    for idx in xrange(1000000):
        fWriteOneGroup(idx)
        sleep(5)

if __name__ == "__main__":
    main()

