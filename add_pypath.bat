:: A handy Windows batch script to set your PYTHONPATH environment variable to include this repos.
:: To use this script you simply need to run this batch script on the command prompt that will execute your python code.

@echo off
set REPO_DIR=%~dp0
set PYTHONPATH=%REPO_DIR%lib;%PYTHONPATH%
