# ============================================================
# DataDev 一键停止（按 PID 文件顺序：前端 → 后端）
# PID 文件 + 进程名校验，杜绝误杀同名进程（架构设计 6.4）
# ============================================================
. "$PSScriptRoot\common.ps1"
$ErrorActionPreference = 'Continue'

function Stop-ByPidFile {
    param([string]$Name)

    $pidFile = Join-Path $RunDir "$Name.pid"
    if (-not (Test-Path $pidFile)) { return }

    $procId = [int](Get-Content $pidFile -ErrorAction SilentlyContinue)
    if ($procId -le 0) { Remove-Item $pidFile -Force -ErrorAction SilentlyContinue; return }

    $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if ($null -eq $proc) {
        Write-Host "[DataDev] $Name 进程不存在（可能已退出），清理 PID 文件" -ForegroundColor Yellow
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
        return
    }

    Write-Step "停止 $Name (PID $procId) ..."
    # 先优雅终止；SQLite 写入为原子事务，无损坏风险
    Stop-Process -Id $procId -ErrorAction SilentlyContinue
    if (-not $proc.WaitForExit(5000)) {
        Write-Host "[DataDev] $Name 未在 5s 内退出，强制终止进程树" -ForegroundColor Yellow
        taskkill /PID $procId /T /F | Out-Null
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    Write-Host "[DataDev] $Name 已停止" -ForegroundColor Green
}

# 兜底清理：uvicorn --reload 的子进程可能成为孤儿，按端口 + 进程名清理（仅限平台自有进程）
function Stop-PortOwner {
    param([int]$Port, [string]$ExpectedProcess, [string]$Name)

    $conn = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($null -eq $conn) { return }
    $ownerId = $conn.OwningProcess
    $proc = Get-Process -Id $ownerId -ErrorAction SilentlyContinue
    if ($null -eq $proc -or $proc.ProcessName -ine $ExpectedProcess) { return }

    Write-Step "清理 $Name 残留进程 (PID $ownerId) ..."
    taskkill /PID $ownerId /T /F | Out-Null
    Write-Host "[DataDev] $Name 残留进程已清理" -ForegroundColor Green
}

Stop-ByPidFile -Name 'frontend'
Stop-ByPidFile -Name 'backend'
Stop-PortOwner -Port 5173 -ExpectedProcess 'node' -Name '前端'
Stop-PortOwner -Port 8000 -ExpectedProcess 'python' -Name '后端'

Write-Step "全部服务已停止"
