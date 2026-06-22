# ==============================================================================
# Google Cloud Run 一键部署 PowerShell 脚本 (deploy-prod.ps1) 
# 使用方式：在 PowerShell 终端运行 .\deploy-prod.ps1 
# ==============================================================================

# 1. 检查是否存在 .env.prod 文件 
$envFile = Join-Path $PSScriptRoot ".env.prod"
if (-not (Test-Path $envFile)) {
    Write-Error "错误：未能在当前目录找到 .env.prod 配置文件！请先创建该文件。 "
    exit 1
}

# 2. 读取并解析 .env.prod 中的环境变量 
$substitutions = @()
$lines = Get-Content $envFile -Encoding UTF8

foreach ($line in $lines) {
    $line = $line.Trim()
    
    # 忽略注释行与空行 
    if ($line.StartsWith("#") -or $line -eq "") {
        continue
    }
    
    # 解析 KEY=VALUE 键值对 
    if ($line -match "^([^=]+)=(.*)$") {
        $key = $Matches[1].Trim()
        $val = $Matches[2].Trim()
        
        # 去除值首尾的双引号或单引号（防止 gcloud 命令接收参数时报错） 
        if ($val.StartsWith('"') -and $val.EndsWith('"')) {
            $val = $val.Substring(1, $val.Length - 2)
        } elseif ($val.StartsWith("'") -and $val.EndsWith("'")) {
            $val = $val.Substring(1, $val.Length - 2)
        }
        
        $substitutions += "$key=$val"
    }
}

# 2.1 动态获取 Git commit 的 short hash 写入 _SHORT_SHA 
$gitSha = $null
try {
    $gitSha = (git rev-parse --short HEAD 2>$null).Trim()
} catch {}

if ($gitSha) {
    $substitutions += "_SHORT_SHA=$gitSha"
}

# 3. 将变量组装为分号分隔的字符串 
$subString = $substitutions -join ";"

# 4. 执行部署 
Write-Host "====================================================" -ForegroundColor Green
Write-Host " 🚀 正在通过本地 .env.prod 文件触发 GCP 一键部署... " -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

# 拼接并执行 gcloud 命令 
$cmd = "gcloud builds submit --config=cloudbuild.yaml --substitutions='^;^$subString'"
Invoke-Expression $cmd
