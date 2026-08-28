@echo off
cd /d "%~dp0"
rem ps1 needs UTF-8 BOM for PowerShell 5.1 Chinese output; repo copy has no BOM, add on first run
powershell -NoProfile -Command "if([IO.File]::ReadAllBytes('%~dp0start_patent_agent.ps1')[0] -ne 0xEF){[IO.File]::WriteAllBytes('%~dp0start_patent_agent.ps1',[byte[]](0xEF,0xBB,0xBF)+[IO.File]::ReadAllBytes('%~dp0start_patent_agent.ps1'))}"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_patent_agent.ps1" %*
pause
