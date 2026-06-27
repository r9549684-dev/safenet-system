# DEPRECATED — используйте: .\build.ps1 -Flavor standard
# build_standard.ps1 — стандартный лёгкий APK (~5 MB, без Hiddify)
# Использование: .\build_standard.ps1

$flutter = "C:\src\flutter\bin\flutter.bat"
$outDir  = "build\app\outputs\flutter-apk"
$outName = "app-standard-release.apk"

Write-Host "=== SafeNet STANDARD build ===" -ForegroundColor Cyan

& $flutter build apk --release
if ($LASTEXITCODE -ne 0) { Write-Host "BUILD FAILED" -ForegroundColor Red; exit 1 }

Copy-Item "$outDir\app-release.apk" "$outDir\$outName" -Force
$size = [math]::Round((Get-Item "$outDir\$outName").Length / 1MB, 1)
Write-Host "OK  $outDir\$outName  ($size MB)" -ForegroundColor Green
