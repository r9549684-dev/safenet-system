# DEPRECATED — используйте: .\build.ps1 -Flavor debug
# build_debug.ps1 — debug APK для тестирования Trojan
# Использование: .\build_debug.ps1

$flutter = "D:\flutter\bin\flutter.bat"
$outDir  = "build\app\outputs\flutter-apk"
$outName = "app-debug-trojan.apk"

Write-Host "=== SafeNet DEBUG build (Trojan) ===" -ForegroundColor Cyan

& $flutter build apk --debug
if ($LASTEXITCODE -ne 0) { Write-Host "BUILD FAILED" -ForegroundColor Red; exit 1 }

Copy-Item "$outDir\app-debug.apk" "$outDir\$outName" -Force
$size = [math]::Round((Get-Item "$outDir\$outName").Length / 1MB, 1)
Write-Host "OK  $outDir\$outName  ($size MB)" -ForegroundColor Green
