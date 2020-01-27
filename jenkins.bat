@ECHO OFF

@ECHO Validation script started: %DATE% %TIME%


ECHO %DATE% %TIME% Checking source code 

CALL "%ROOT_PATH% pylint application || EXIT 1
