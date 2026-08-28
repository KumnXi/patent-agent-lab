@echo off
cd /d "%~dp0"
rem ps1 需 UTF-8 BOM 才能在 PowerShell 5.1 下正确显示中文；仓库内无 BOM，首次运行自动补
powershell -NoProfile -Command "$p='%~dp0start_patent_agent.ps1'; $b=[IO.File]::ReadAllBytes($p); if($b.Length -gt 3 -and $b[0] -ne 0xEF){ [IO.File]::WriteAllBytes($p, [byte[]](0xEF,0xBB,0xBF)+$b) }"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_patent_agent.ps1" %*
pause
