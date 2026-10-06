# Prepare ResQGrid AI for Android Studio testing
# Usage:
#   .\prepare-android-studio.ps1 emulator    # for Android Emulator (uses 10.0.2.2)
#   .\prepare-android-studio.ps1 device     # for physical device (auto-detects PC IP)

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("emulator", "device")]
    [string]$Target
)

$ErrorActionPreference = "Stop"

if ($Target -eq "emulator") {
    # 10.0.2.2 is the emulator's alias for the host computer's localhost
    $ApiUrl = "http://10.0.2.2:8000/api/v1"
} else {
    $localIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" } | Select-Object -First 1).IPAddress
    if (-not $localIp) {
        throw "Could not detect local IP. Make sure Wi-Fi/Ethernet is connected."
    }
    $ApiUrl = "http://$localIp`:8000/api/v1"
}

Write-Host "Preparing Android Studio build for $Target" -ForegroundColor Cyan
Write-Host "API URL will be: $ApiUrl" -ForegroundColor Cyan

$env:BUILD_FOR_CAPACITOR = "true"
$env:NEXT_PUBLIC_API_URL = $ApiUrl
$env:NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = ""
$env:NEXT_PUBLIC_MAP_STYLE_URL = "https://tiles.openfreemap.org/styles/liberty"

npm run build
npx cap sync android

Write-Host "Done. Open apps/web/android in Android Studio and click Run." -ForegroundColor Green
