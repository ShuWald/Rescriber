# Kill any existing Chrome instance using the dev profile (requires WMI for CommandLine access)
Get-CimInstance Win32_Process -Filter "name = 'chrome.exe'" | Where-Object {
    $_.CommandLine -like "*ChromeDevProfile*"
} | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Milliseconds 2000

Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList `
    "--ignore-certificate-errors", `
    "--allow-insecure-localhost", `
    "--user-data-dir=$env:LOCALAPPDATA\Google\ChromeDevProfile"
