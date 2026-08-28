@echo off
cd /d "%~dp0"
rem ps1 needs UTF-8 BOM for PowerShell 5.1 Chinese output; repo copy has no BOM, add on first run
powershell -NoProfile -Command "$p='%~dp0start_patent_agent.ps1'; $b=[IO.File]::ReadAllBytes($p); if($b.Length -gt 3 -and $b[0] -ne 0xEF){ [IO.File]::WriteAllBytes($p, [byte[]](0xEF,0xBB,0xBF)+$b) }"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_patent_agent.ps1" %*
pause
