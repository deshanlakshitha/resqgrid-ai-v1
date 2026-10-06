# Build ResQGrid AI Android APK (debug)
# Requires: Android SDK (ANDROID_HOME) and Java JDK

param(
    [string]$ApiUrl = "",
    [switch]$Release
)

$ErrorActionPreference = "Stop"

# Detect local IP if no API URL provided
if (-not $ApiUrl) {
    $localIp = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "*Wi-Fi*" -ErrorAction SilentlyContinue | Select-Object -First 1).IPAddress
    if (-not $localIp) {
        $localIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" } | Select-Object -First 1).IPAddress
    }
    if (-not $localIp) {
        throw "Could not detect local IP. Please pass -ApiUrl http://<your-ip>:8000/api/v1"
    }
    $ApiUrl = "http://$localIp`:8000/api/v1"
}

Write-Host "Building APK with API URL: $ApiUrl" -ForegroundColor Cyan

# Build static web assets
$env:BUILD_FOR_CAPACITOR = "true"
$env:NEXT_PUBLIC_API_URL = $ApiUrl
$env:NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = ""
$env:NEXT_PUBLIC_MAP_STYLE_URL = "https://tiles.openfreemap.org/styles/liberty"

npm run build

# Sync with Capacitor Android project
npx cap sync android

# Build APK with Gradle
$gradle = if (Test-Path "$env:ANDROID_HOME\gradle\bin\gradle") { "$env:ANDROID_HOME\gradle\bin\gradle" } else { ".\android\gradlew" }
$task = if ($Release) { "assembleRelease" } else { "assembleDebug" }

& $gradle -p .\android $task

if ($Release) {
    Write-Host "APK: .\android\app\build\outputs\apk\release\app-release-unsigned.apk" -ForegroundColor Green
} else {
    Write-Host "APK: .\android\app\build\outputs\apk\debug\app-debug.apk" -ForegroundColor Green
}
