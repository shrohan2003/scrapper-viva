@echo off
setlocal
cd /d "%~dp0"
if errorlevel 1 exit /b 1

py -3 -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>&1
if not errorlevel 1 goto use_py

python -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>&1
if not errorlevel 1 goto use_python

echo Python 3.11 or newer was not found.
echo Install Python from https://www.python.org/downloads/ and enable Add Python to PATH if offered.
echo Then close this window and run START_HERE.bat again.
set "scrapper_status=1"
goto finish

:use_py
py -3 start.py %*
set "scrapper_status=%errorlevel%"
goto finish

:use_python
python start.py %*
set "scrapper_status=%errorlevel%"

:finish
if not "%~1"=="" goto return_status
echo.
pause
:return_status
exit /b %scrapper_status%
