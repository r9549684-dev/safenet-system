# build.ps1 — Единая точка входа для сборки SafeNet APK
# Использование:
#   .\build.ps1 -Flavor standard
#   .\build.ps1 -Flavor iran
#   .\build.ps1 -Flavor china
#   .\build.ps1 -Flavor debug
#   .\build.ps1 -Flavor standard -ApiUrl "http://38.180.253.219:8001"
#
# DEPRECATED: build_standard.ps1, build_iran.ps1, build_china.ps1, build_debug.ps1

param(
    [Parameter(Mandatory)]
    [ValidateSet('standard','iran','china','debug')]
    [string]$Flavor,

    [string]$ApiUrl = 'https://safenetsystem.duckdns.org'
)

$ErrorActionPreference = 'Stop'

$flutter = "C:\src\flutter\bin\flutter.bat"
$outDir  = "build\app\outputs\flutter-apk"
$srcSingbox   = "assets\singbox\sing-box-arm64"
$srcTun2socks = "assets\singbox\tun2socks-arm64"
$jniDir       = "android\app\src\main\jniLibs\arm64-v8a"
$libSingbox   = "$jniDir\libsingbox.so"
$libTun2socks = "$jniDir\libtun2socks.so"

$bundleHiddify = $Flavor -in @('iran','china')
$buildMode = if ($Flavor -eq 'debug') { '--debug' } else { '--release' }

Write-Host "=== SafeNet $Flavor build ===" -ForegroundColor Cyan
Write-Host "Flavor:        $Flavor" -ForegroundColor Yellow
Write-Host "API URL:       $ApiUrl" -ForegroundColor Yellow
Write-Host "BUNDLE_HIDDIFY: $bundleHiddify" -ForegroundColor Yellow
Write-Host "Mode:          $buildMode" -ForegroundColor Yellow

try {
    if ($bundleHiddify) {
        New-Item -ItemType Directory -Force -Path $jniDir | Out-Null
        Copy-Item $srcSingbox   $libSingbox   -Force
        Copy-Item $srcTun2socks $libTun2socks -Force
        Write-Host "libsingbox.so + libtun2socks.so: скопированы в $jniDir" -ForegroundColor Yellow
    }

    $dartDefines = @(
        "--dart-define=API_BASE_URL=$ApiUrl",
        "--dart-define=BUNDLE_HIDDIFY=$bundleHiddify"
    )

    & $flutter build apk $buildMode @dartDefines
    if ($LASTEXITCODE -ne 0) { throw "Flutter build failed" }

    $srcApk = if ($Flavor -eq 'debug') {
        "$outDir\app-debug.apk"
    } else {
        "$outDir\app-release.apk"
    }
    $outName = "app-$Flavor-release.apk"
    Copy-Item $srcApk "$outDir\$outName" -Force

    $size = [math]::Round((Get-Item "$outDir\$outName").Length / 1MB, 1)
    $hash = (Get-FileHash "$outDir\$outName" -Algorithm SHA256).Hash
    Write-Host "OK  $outDir\$outName  ($size MB)" -ForegroundColor Green
    Write-Host "SHA256: $hash" -ForegroundColor Gray

    $registry = "D:\SafeNet\build_registry.csv"
    if (-not (Test-Path $registry)) {
        "Date,Flavor,Version,SizeMB,SHA256,ApiUrl" | Out-File $registry -Encoding utf8
    }
    $version = (Select-String -Path "pubspec.yaml" -Pattern "^version:" | Select-Object -First 1).Line -replace "^version:\s*",""
    "$(Get-Date -Format s),$Flavor,$version,$size,$hash,$ApiUrl" | Out-File $registry -Append -Encoding utf8
    Write-Host "Записано в реестр: $registry" -ForegroundColor Gray
}
finally {
    if ($bundleHiddify) {
        Remove-Item $libSingbox   -Force -ErrorAction SilentlyContinue
        Remove-Item $libTun2socks -Force -ErrorAction SilentlyContinue
        Write-Host "jniLibs: восстановлен" -ForegroundColor Yellow
    }
}
