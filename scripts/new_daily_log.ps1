param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd")
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$templatePath = Join-Path $projectRoot "docs\templates\DAILY_LOG_TEMPLATE.md"
$dailyDirectory = Join-Path $projectRoot "docs\daily"
$dailyPath = Join-Path $dailyDirectory "$Date.md"

if (-not (Test-Path -LiteralPath $templatePath)) {
    throw "找不到每日记录模板：$templatePath"
}

if (Test-Path -LiteralPath $dailyPath) {
    Write-Host "今日记录已存在：$dailyPath"
    exit 0
}

New-Item -ItemType Directory -Path $dailyDirectory -Force | Out-Null
$content = Get-Content -LiteralPath $templatePath -Raw -Encoding UTF8
$content = $content.Replace("YYYY-MM-DD", $Date)
[System.IO.File]::WriteAllText($dailyPath, $content, [System.Text.UTF8Encoding]::new($false))

Write-Host "已创建每日记录：$dailyPath"

