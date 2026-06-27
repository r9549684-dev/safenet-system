# DEPRECATED — используйте: .\build.ps1 -Flavor china
# build_china.ps1 — China APK (VLESS+Reality+Fragment + AmneziaWG + ByeDPI)
# Использование: .\build_china.ps1
# Временно помещает sing-box в jniLibs/arm64-v8a/libsingbox.so,
# собирает APK, затем удаляет временный файл.

$flutter      = "C:\src\flutter\bin\flutter.bat"
$outDir       = "build\app\outputs\flutter-apk"
$outName      = "app-china-release.apk"
$srcSingbox   = "assets\singbox\sing-box-arm64"
$srcTun2socks = "assets\singbox\tun2socks-arm64"
$jniDir       = "android\app\src\main\jniLibs\arm64-v8a"
$libSingbox   = "$jniDir\libsingbox.so"
$libTun2socks = "$jniDir\libtun2socks.so"

Write-Host "=== SafeNet CHINA build ===" -ForegroundColor Cyan

# 1. Копируем бинарники как native libs
New-Item -ItemType Directory -Force -Path $jniDir | Out-Null
Copy-Item $srcSingbox   $libSingbox   -Force
Copy-Item $srcTun2socks $libTun2socks -Force
Write-Host "libsingbox.so + libtun2socks.so: скопированы в $jniDir" -ForegroundColor Yellow

try {
    # 2. Собираем с флагом BUNDLE_HIDDIFY=true (Максимальный режим → VLESS+Reality)
    & $flutter build apk --release --dart-define=BUNDLE_HIDDIFY=true
    if ($LASTEXITCODE -ne 0) { throw "Flutter build failed" }

    # 3. Копируем результат с новым именем
    Copy-Item "$outDir\app-release.apk" "$outDir\$outName" -Force
    $size = [math]::Round((Get-Item "$outDir\$outName").Length / 1MB, 1)
    Write-Host "OK  $outDir\$outName  ($size MB)" -ForegroundColor Green
}
finally {
    # 4. Удаляем временные файлы
    Remove-Item $libSingbox   -Force -ErrorAction SilentlyContinue
    Remove-Item $libTun2socks -Force -ErrorAction SilentlyContinue
    Write-Host "jniLibs: восстановлен" -ForegroundColor Yellow
}
