# ============================================================
# DataDev 一键启动（prod / dev 双模式）
# 用法：.\scripts\start.ps1 -Mode dev [-Port 8000]
# ============================================================
param(
    [ValidateSet('prod', 'dev')][string]$Mode = 'prod',
    [int]$Port = 8000
)

. "$PSScriptRoot\common.ps1"
Ensure-Dirs

# 端口可经环境变量覆盖（规则 01）
if ($env:DATAFLOW_PORT) { $Port = [int]$env:DATAFLOW_PORT }

Write-Step "启动模式: $Mode，后端端口: $Port"

# ---------- 1. 前置检查：端口占用 ----------
if (Test-PortBusy -Port $Port) {
    Write-Host "[DataDev] 端口 $Port 已被占用: $(Get-PortOwner -Port $Port)，请先停止占用进程" -ForegroundColor Red
    exit 1
}
if ($Mode -eq 'dev' -and (Test-PortBusy -Port 5173)) {
    Write-Host "[DataDev] 端口 5173 已被占用: $(Get-PortOwner -Port 5173)" -ForegroundColor Red
    exit 1
}

# ---------- 2. Python 虚拟环境 ----------
$venvDir = Join-Path $BackendDir '.venv'
if (-not (Test-Path (Join-Path $venvDir 'Scripts\python.exe'))) {
    Write-Step "创建 Python 虚拟环境 .venv ..."
    python -m venv $venvDir
    if ($LASTEXITCODE -ne 0) { Write-Host "[DataDev] 创建 venv 失败" -ForegroundColor Red; exit 1 }
}
$pythonExe = Join-Path $venvDir 'Scripts\python.exe'

# ---------- 3. 安装依赖 ----------
Write-Step "检查并安装后端依赖 ..."
& $pythonExe -m pip install -q -r (Join-Path $BackendDir 'requirements.txt')
if ($LASTEXITCODE -ne 0) { Write-Host "[DataDev] pip install 失败" -ForegroundColor Red; exit 1 }

# ---------- 4. config.yaml 兜底复制 ----------
$cfg = Join-Path $BackendDir 'config.yaml'
if (-not (Test-Path $cfg)) {
    Write-Step "未发现 config.yaml，从 config.example.yaml 复制（密码请用环境变量注入）"
    Copy-Item (Join-Path $BackendDir 'config.example.yaml') $cfg
}

# ---------- 5. 初始化数据库（幂等建表） ----------
Write-Step "初始化数据库表结构 ..."
Push-Location $BackendDir
try {
    & $pythonExe -c "import asyncio; from app.core.database import init_db; asyncio.run(init_db())"
    if ($LASTEXITCODE -ne 0) { Write-Host "[DataDev] 数据库初始化失败" -ForegroundColor Red; exit 1 }
} finally {
    Pop-Location
}

# ---------- 6. 启动后端 uvicorn ----------
$logFile  = Join-Path $LogDir 'backend.log'
$errFile  = Join-Path $LogDir 'backend.err.log'
Rotate-Log -Path $logFile
Rotate-Log -Path $errFile

Write-Step "启动后端 uvicorn (127.0.0.1:$Port) ..."
$uvicornArgs = @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', "$Port")
if ($Mode -eq 'dev') { $uvicornArgs += '--reload' }

$proc = Start-Process -FilePath $pythonExe -ArgumentList $uvicornArgs `
    -WorkingDirectory $BackendDir `
    -RedirectStandardOutput $logFile -RedirectStandardError $errFile `
    -PassThru -WindowStyle Hidden
$proc.Id | Out-File (Join-Path $RunDir 'backend.pid') -Encoding ascii

# ---------- 7. 健康检查（最多等待 30s） ----------
Write-Step "等待健康检查 GET /api/v1/health ..."
$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/health" -TimeoutSec 2
        if ($resp.code -eq 0) { $healthy = $true; break }
    } catch { }
}
if (-not $healthy) {
    Write-Host "[DataDev] 后端健康检查失败，请查看日志: $errFile" -ForegroundColor Red
    exit 1
}
Write-Host "[DataDev] 后端已就绪 (PID $($proc.Id))" -ForegroundColor Green

# ---------- 8. [dev] 启动前端 Vite ----------
if ($Mode -eq 'dev') {
    Write-Step "启动前端 Vite dev (5173) ..."
    $feLog = Join-Path $LogDir 'frontend.log'
    $feErr = Join-Path $LogDir 'frontend.err.log'
    Rotate-Log -Path $feLog
    Rotate-Log -Path $feErr
    $npmCmd = (Get-Command npm.cmd).Source
    $feProc = Start-Process -FilePath $npmCmd -ArgumentList @('run', 'dev') `
        -WorkingDirectory $FrontendDir `
        -RedirectStandardOutput $feLog -RedirectStandardError $feErr `
        -PassThru -WindowStyle Hidden
    $feProc.Id | Out-File (Join-Path $RunDir 'frontend.pid') -Encoding ascii
    Write-Host "[DataDev] 前端已启动 (PID $($feProc.Id))" -ForegroundColor Green
    Write-Host ""
    Write-Host "  访问地址: http://127.0.0.1:5173" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "  访问地址: http://127.0.0.1:$Port" -ForegroundColor Yellow
}
Write-Host "  日志目录: $LogDir" -ForegroundColor Yellow
Write-Host "  停止服务: .\scripts\stop.ps1" -ForegroundColor Yellow
