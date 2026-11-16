# Cai skill edit-capcut-AI tren may moi bang 1 lenh (khong can gui file):
#   powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/phamthilyntnd-sketch/edit-capcut-AI/main/cai-dat/tai-va-cai.ps1 | iex"
# Tai CAI-DAT.cmd moi nhat tu GitHub ve thu muc tam roi chay no.
# (Chi dung khi repo cong khai. Repo rieng tu: gui file CAI-DAT.cmd cho nhan su.)
$ErrorActionPreference = "Stop"
$url = "https://raw.githubusercontent.com/phamthilyntnd-sketch/edit-capcut-AI/main/cai-dat/CAI-DAT.cmd"
$f = Join-Path $env:TEMP "CAI-DAT-edit-capcut-ai.cmd"
Write-Host "== Dang tai bo cai edit-capcut-AI..." -ForegroundColor Cyan
try {
    $txt = (Invoke-WebRequest -Uri $url -UseBasicParsing).Content
} catch {
    Write-Host "[LOI] Khong tai duoc bo cai (mat mang, hoac repo dang rieng tu -> xin file CAI-DAT.cmd tu quan ly)." -ForegroundColor Red
    return
}
if ($txt -is [byte[]]) { $txt = [System.Text.Encoding]::UTF8.GetString($txt) }
$txt = ($txt -replace "`r?`n", "`r`n")                                   # .cmd can xuong dong Windows
[System.IO.File]::WriteAllText($f, $txt, (New-Object System.Text.UTF8Encoding $false))   # UTF-8 khong BOM
Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$f`"" -Wait
