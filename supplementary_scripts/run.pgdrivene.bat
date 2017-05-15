
ECHO off

REM Note: had to remove single
REM quotes from lhs of these assignments,
REM as python read their values in
REM with the quotes

set myf=py3.test2.wf.r1.genepop
set popscheme=none
set popparam=none
set popmin=1
set popmax=99999
set poprange=1-99999
set freq=0.01
set popreps=1
set locscheme=none
set locparam=none
set locmin=1
set locmax=99999
set locrange=1-99999
set locreps=1
set procs=2
set mode=testserial
set nbrat=None
set dobias=False


REM [-h] -f GPFILES -s SCHEME -p PARAMS -m MINPOPSIZE
REM -a MAXPOPSIZE -r POPRANGE -e MINALLELEFREQ -c
REM REPLICATES -l LOCISCHEME -i LOCISCHEMEPARAMS -n
REM MINTOTALLOCI -x MAXTOTALLOCI -g LOCIRANGE -q
REM LOCIREPLICATES [-o PROCESSES] [-d MODE]
REM [-b NBNERATIO] [-j DONBBIASADJUST]

python ../pgdriveneestimator.py -f %myf% ^
				-s %popscheme% ^
				-p %popparam% ^
				-m %popmin% ^
				-a %popmax% ^
				-r %poprange% ^
				-e %freq% ^
				-c %popreps% ^
				-l %locscheme% ^
				-i %locparam% ^
				-n %locmin% ^
				-x %locmax% ^
				-g %locrange% ^
				-q %locreps% ^
				-o %procs% ^
				-d %mode% ^
				-b %nbrat% ^
				-j %dobias%

		
