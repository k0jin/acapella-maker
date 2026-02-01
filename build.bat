@echo off
REM build.bat - Windows batch wrapper for build.ps1
REM Usage: build.bat [options]
REM Run build.bat --help for available options

powershell -ExecutionPolicy Bypass -File "%~dp0build.ps1" %*
