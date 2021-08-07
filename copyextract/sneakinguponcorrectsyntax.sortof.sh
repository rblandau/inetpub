C:\cygwin64\bin\bash.exe -l -c "(cd /cygdrive/d/Inetpub/Scripts; echo foo2>test1output2.log; ls -l >test1output3.log;) "

C:\cygwin64\bin\bash.exe -l -c "(cd /cygdrive/d/Inetpub/Scripts; date +%Y%m%d_%H%M%S >test1output2.log; ls -l >test1output3.log;) "

C:\cygwin64\bin\bash.exe -l -c "(cd /cygdrive/d/Inetpub/Scripts; date +%Y%m%d_%H%M%S >test1output2.log; ls -l >test1output3.log; python CheckNetPy.py 1 test1output4.log) "


C:\cygwin64\bin\bash.exe -l -c "(cd /cygdrive/d/Inetpub/Scripts; date +%Y%m%d_%H%M%S >test2_checknetstartmaybe.log; sh checknetpy_start.sh >> test2_checknetstartmaybe.log) "

C:\cygwin64\bin\bash.exe -l -c "(cd /cygdrive/d/Inetpub/Scripts; date +%Y%m%d_%H%M%S >test3_maybe.log; python3 checknetpy3.py test3_checknetonceonly.log) "


C:\cygwin64\bin\bash.exe -l -c "(cd /cygdrive/d/Inetpub/Scripts; date +%Y%m%d_%H%M%S >test3_maybe.log; sh repeatthis.sh 'python3 checknetpy3.py test3_checknetonceonly.log' 60 3) "


C:\cygwin64\bin\bash.exe -l -c "(cd /cygdrive/d/Inetpub/Scripts; date +%Y%m%d_%H%M%S >test3_maybe.log; sh repeatthis.sh 'python3 checknetpy3.py checknetpy3.log' 900) "


C:\cygwin64\bin\bash.exe -l -c "(cd /cygdrive/d/Inetpub/Scripts; date +%Y%m%d_%H%M%S >test4_maybe.log; bash repeatthis.sh 'ls >>test4_maybe.log; ' 10 2; date +%Y%m%d_%H%M%S >>test4_maybe.log;) "

C:\cygwin64\bin\bash.exe -l -c "(cd /cygdrive/d/Inetpub/Scripts; date +%Y%m%d_%H%M%S >test4_maybe.log; sh repeatthis.sh 'sh copylogextract.sh ' 10 2) "



CMD /C dir s: > d:\dir-s.txt
# Fails!  dir works, redirect works, output is empty, length=0 bytes.  
# Conclusion: any service on windows is not permitted to touch any disk 
#  that is not physically installed on the system, that is, no touchee
#  network drives.  Oh, poo.  
#  Find another way to do this, e.g., as a boot startup script, but not a service.  
# 

