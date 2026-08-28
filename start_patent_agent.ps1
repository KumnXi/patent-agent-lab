param(
    [switch]$SetupOnly  # 干跑：只做检查与渲染，不启动服务（调试用）
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ""
Write-Host "=============================================="
Write-Host "  专利撰写 Agent - 一键启动"
Write-Host "=============================================="
Write-Host ""

# -- 1. 检查 Node.js --
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Host "[X] 未检测到 Node.js（agent 框架 dsh 的运行底座）" -ForegroundColor Red
    Write-Host "    请到 https://nodejs.org/ 下载安装 LTS 版，装完重新双击 启动专利Agent.bat"
    exit 1
}
Write-Host "[1/5] Node.js OK  $((node -v))"

# -- 2. 检查/生成配置文件 --
$cfgPath = Join-Path $root "config\settings.local.json"
$example = Join-Path $root "config\settings.example.json"
if (-not (Test-Path $cfgPath)) {
    Copy-Item $example $cfgPath
    Write-Host "[!] 首次使用：已生成配置文件 config\settings.local.json" -ForegroundColor Yellow
    Start-Process notepad $cfgPath
    Write-Host ""
    Write-Host "    请在打开的记事本里填好三项后保存："
    Write-Host "      patent_project_path  专利撰写助手(patent-aid)项目的本地路径"
    Write-Host "      python               该项目可用的 python.exe（需装好它的 requirements）"
    Write-Host "      deepseek_api_key     你的 DeepSeek API Key（sk- 开头）"
    Write-Host ""
    Write-Host "    填完保存，重新双击 启动专利Agent.bat 即可。"
    exit 0
}
$cfg = [IO.File]::ReadAllText($cfgPath, [Text.Encoding]::UTF8) | ConvertFrom-Json

# -- 3. 校验配置 --
if (-not (Test-Path $cfg.python)) {
    Write-Host "[X] 配置里的 python 路径不存在: $($cfg.python)" -ForegroundColor Red
    Write-Host "    请打开 config\settings.local.json 修改"
    exit 1
}
$proj = $cfg.patent_project_path
if (-not (Test-Path (Join-Path $proj "src\core\__init__.py"))) {
    Write-Host "[X] 专利撰写助手项目路径不对: $proj" -ForegroundColor Red
    Write-Host "    （需要能在该目录下找到 src\core\__init__.py）"
    Write-Host "    还没有该项目？git clone https://github.com/KumnXi/patent-aid"
    Write-Host "    并按它的 README 装好依赖与数据库"
    exit 1
}
if ($cfg.deepseek_api_key -notmatch "^sk-" -or $cfg.deepseek_api_key -like "*REPLACE_ME*") {
    Write-Host "[X] deepseek_api_key 还没填（sk- 开头，platform.deepseek.com 免费注册申请）" -ForegroundColor Red
    Start-Process notepad $cfgPath
    exit 1
}
Write-Host "[2/5] 配置 OK"

# -- 4. 环境变量 + mcp 依赖 --
$env:PATENT_PROJECT_PATH = $proj
$env:PATENT_PYTHON = $cfg.python
$env:DEEPSEEK_API_KEY = $cfg.deepseek_api_key
$env:DSH_PERMISSION_MODE = "danger-full-access"
$env:PYTHONUTF8 = "1"

& $cfg.python -c "import mcp" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[3/5] 正在安装 mcp 依赖（仅首次，约 1 分钟）..."
    & $cfg.python -m pip install "mcp<2" --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] mcp 安装失败，请手动执行: $($cfg.python) -m pip install `"mcp<2`"" -ForegroundColor Red
        exit 1
    }
}
Write-Host "[3/5] mcp 依赖 OK"

# -- 5. 渲染 dsh overlay --
# 编码一律用 .NET 显式 UTF-8：PS5.1 的 Get-Content -Encoding UTF8 在部分环境
# 会按 GBK 解码（实测踩坑），生成 YAML 里的中文路径会乱码
$tpl = [IO.File]::ReadAllText((Join-Path $root ".cordis.yml.template"), [Text.Encoding]::UTF8)
$server = (Join-Path $root "mcp_server\patent_server.py") -replace "\\", "/"
$pyFwd = $cfg.python -replace "\\", "/"
$projFwd = $proj -replace "\\", "/"
$render = $tpl.Replace("{{PYTHON}}", $pyFwd)
$render = $render.Replace("{{SERVER}}", $server)
$render = $render.Replace("{{OLD_PROJECT}}", $projFwd)
[IO.File]::WriteAllText((Join-Path $root ".cordis.local.yml"), $render, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "[4/5] MCP overlay 已生成 (.cordis.local.yml)"

Write-Host "[5/5] 预检完成"
if ($SetupOnly) {
    Write-Host "SetupOnly 干跑结束，一切正常。" -ForegroundColor Green
    exit 0
}

# -- 启动 --
Write-Host ""
Write-Host "启动服务中... 浏览器将自动打开 http://127.0.0.1:3080"
Write-Host "停止服务：关闭本窗口即可"
Write-Host ""
& npx -y "@deepseek-ai/dsh" --profile web --patch "$root\.cordis.local.yml"
