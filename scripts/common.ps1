# ============================================================
# DataDev 公共函数：start.ps1 / stop.ps1 共用（规则 01：统一脚本入口）
# ============================================================
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir  = Join-Path $ProjectRoot 'backend'
$FrontendDir = Join-Path $ProjectRoot 'frontend'
$LogDir      = Join-Path $ProjectRoot 'logs'
$RunDir      = Join-Path $ProjectRoot 'data\run'

function Ensure-Dirs {
    foreach ($d in @($LogDir, $RunDir)) {
        if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    }
}

# 端口占用检查（占用即返回 true，不做强杀）
function Test-PortBusy {
    param([int]$Port)
    $conn = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    return ($null -ne $conn)
}

function Get-PortOwner {
    param([int]$Port)
    $conn = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($null -eq $conn) { return '' }
    $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    if ($null -eq $proc) { return "PID $($conn.OwningProcess)" }
    return "$($proc.ProcessName) (PID $($conn.OwningProcess))"
}

function Write-Step {
    param([string]$Message)
    Write-Host "[DataDev] $Message" -ForegroundColor Cyan
}

function Get-VenvPython {
    $venvPython = Join-Path $BackendDir '.venv\Scripts\python.exe'
    if (Test-Path $venvPython) { return $venvPython }
    return 'python'
}

# 日志轮转：超过 50MB 重命名归档（rules/架构设计 6.4）
function Rotate-Log {
    param([string]$Path)
    if (Test-Path $Path) {
        $size = (Get-Item $Path).Length
        if ($size -gt 50MB) {
            $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
            Rename-Item $Path "$Path.$stamp.old"
        }
    }
}
