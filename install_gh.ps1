[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$url = "https://github.com/cli/cli/releases/download/v2.67.0/gh_2.67.0_windows_amd64.msi"
$out = "$env:TEMP\gh.msi"
(New-Object Net.WebClient).DownloadFile($url, $out)
Start-Process msiexec.exe -ArgumentList "/i", $out, "/quiet", "/norestart" -Wait -NoNewWindow
Write-Output "GitHub CLI installed"
