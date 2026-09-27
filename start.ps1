<#
.SYNOPSIS
    BidAlert 一键启动脚本
.DESCRIPTION
    自动检查环境依赖，同时启动后端(FastAPI :8000)和前端(Vite :3000)，并打开浏览器。
.NOTES
    按 Ctrl+C 停止所有服务。
#>

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$BackendUrl = "http://127.0.0.1:8000"
$FrontendUrl = "http://localhost:3000"

function Write-Step($msg) { Write-Host "[BidAlert] $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "[BidAlert] $msg" -ForegroundColor Green }
function Write-Err($msg)  { Write-Host "[BidAlert] $msg" -ForegroundColor Red }

# ---------- 环境检查 ----------

Write-Step "检查运行环境..."

# Python
$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCmd) {
    $pyCmd = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $pyCmd) {
    Write-Err "未找到 Python，请先安装 Python 3.11+ 并加入 PATH。"
    exit 1
}
$pyVer = & $pyCmd.Source --version 2>&1
Write-OK "Python: $pyVer"

# Node.js
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Err "未找到 Node.js，请先安装 Node.js 18+ 并加入 PATH。"
    exit 1
}
$nodeVer = & $nodeCmd.Source --version 2>&1
Write-OK "Node.js: $nodeVer"

# ---------- 后端依赖检查 ----------

Write-Step "检查后端依赖..."
$needInstall = $false
foreach ($pkg in @("fastapi", "uvicorn", "sqlalchemy", "openpyxl", "pydantic")) {
    $check = & $pyCmd.Source -c "import $pkg" 2>&1
    if ($LASTEXITCODE -ne 0) { $needInstall = $true; break }
}
if ($needInstall) {
    Write-Step "安装后端依赖（首次启动较慢，请耐心等待）..."
    & $pyCmd.Source -m pip install -r (Join-Path $Backend "requirements.txt") --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Err "后端依赖安装失败，请手动执行：cd backend; python -m pip install -r requirements.txt"
        exit 1
    }
    Write-OK "后端依赖安装完成"
} else {
    Write-OK "后端依赖已就绪"
}

# ---------- 前端依赖检查 ----------

Write-Step "检查前端依赖..."
if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    Write-Step "安装前端依赖（首次启动较慢，请耐心等待）..."
    Push-Location $Frontend
    try {
        npm install --silent 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Err "前端依赖安装失败，请手动执行：cd frontend; npm install"
            exit 1
        }
        Write-OK "前端依赖安装完成"
    } finally {
        Pop-Location
    }
} else {
    Write-OK "前端依赖已就绪"
}

# ---------- 端口检查 ----------

Write-Step "检查端口占用..."
$port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
$port3000 = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if ($port8000) { Write-Err "端口 8000 已被占用（后端）"; exit 1 }
if ($port3000) { Write-Err "端口 3000 已被占用（前端）"; exit 1 }
Write-OK "端口 8000、3000 均空闲"

# ---------- 启动服务 ----------

$jobs = @()

# 启动后端
Write-Step "启动后端服务 (FastAPI :8000)..."
$backendJob = Start-Process -FilePath $pyCmd.Source `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $Backend `
    -WindowStyle Minimized `
    -PassThru
$jobs += $backendJob
Write-OK "后端进程已启动 (PID: $($backendJob.Id))"

# 启动前端
Write-Step "启动前端服务 (Vite :3000)..."
$npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npmCmd) { $npmCmd = "npm" }
$frontendJob = Start-Process -FilePath $npmCmd `
    -ArgumentList "run", "dev" `
    -WorkingDirectory $Frontend `
    -WindowStyle Minimized `
    -PassThru
$jobs += $frontendJob
Write-OK "前端进程已启动 (PID: $($frontendJob.Id))"

# ---------- 等待服务就绪 ----------

Write-Step "等待服务就绪..."
$maxWait = 30
$backendReady = $false
$frontendReady = $false

for ($i = 1; $i -le $maxWait; $i++) {
    Start-Sleep -Seconds 1
    if (-not $backendReady) {
        try {
            $client = New-Object System.Net.WebClient
            $null = $client.DownloadString("$BackendUrl/")
            $backendReady = $true
            Write-OK "后端服务就绪"
        } catch { }
    }
    if (-not $frontendReady) {
        try {
            $conn = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction Stop
            if ($conn) {
                $frontendReady = $true
                Write-OK "前端服务就绪"
            }
        } catch { }
    }
    if ($backendReady -and $frontendReady) { break }
    if ($i % 5 -eq 0) { Write-Host "  等待中... ($i 秒)" -ForegroundColor DarkGray }
}

if (-not $backendReady) { Write-Err "后端启动超时，请检查 backend/ 目录下是否有报错" }
if (-not $frontendReady) { Write-Err "前端启动超时，请检查 frontend/ 目录下是否有报错" }

# ---------- 打开浏览器 ----------

if ($frontendReady) {
    Write-Step "打开浏览器..."
    Start-Process $FrontendUrl
    Write-OK "浏览器已打开: $FrontendUrl"
}

# ---------- 输出信息 ----------

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  BidAlert 已启动" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  前端地址:  $FrontendUrl" -ForegroundColor White
Write-Host "  后端API:   $BackendUrl/docs" -ForegroundColor White
Write-Host "  API文档:   $BackendUrl/docs" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  按 Ctrl+C 停止所有服务" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ---------- 等待退出 ----------

try {
    while ($true) {
        Start-Sleep -Seconds 1
        foreach ($job in $jobs) {
            if ($job.HasExited) {
                Write-Err "进程 $($job.Id) 已退出（退出码: $($job.ExitCode)）"
                throw "服务异常退出"
            }
        }
    }
} finally {
    Write-Step "正在停止所有服务..."
    foreach ($job in $jobs) {
        if (-not $job.HasExited) {
            Stop-Process -Id $job.Id -Force -ErrorAction SilentlyContinue
        }
    }
    # 递归终止子进程（uvicorn / node）
    Get-Process -Name python, node, uvicorn -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -like "*$Root*" -or $_.Path -like "*python*" } |
        Stop-Process -Force -ErrorAction SilentlyContinue
    Write-OK "所有服务已停止"
}
