# Bộ cài TỰ ĐỘNG skill edit-capcut-AI cho máy mới (Windows 10/11, PowerShell 5.1+).
# Nhân sự chỉ cần chạy 1 lệnh (xem README) — script tự tải và cài mọi thứ theo cai-dat\lien-ket.json:
#   Git, Python, Node.js, ffmpeg, Chrome (nếu thiếu, qua winget) · skill từ GitHub · thư viện Python · capcut-cli
#   · mô hình tách người u2net · mô hình nghe tiếng Việt Whisper · bộ tiếng nhấn · kiểm máy.
# Chạy lại bất cứ lúc nào để CẬP NHẬT skill (git pull) — không mất cấu hình máy (may.json).
# Tham số: -KiemTra  = chỉ kiểm, không cài gì.   -ThuMuc <đường dẫn> = nơi đặt skill (mặc định ~\.claude\skills\edit-capcut-ai)
param([switch]$KiemTra, [string]$ThuMuc = "")

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Buoc($t) { Write-Host ""; Write-Host "== $t" -ForegroundColor Cyan }
function Ok($t) { Write-Host "   [OK] $t" -ForegroundColor Green }
function Canh($t) { Write-Host "   [!] $t" -ForegroundColor Yellow }
function CoLenh($n) { return [bool](Get-Command $n -ErrorAction SilentlyContinue) }
function LamMoiPath {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}

# --- danh sách link: lấy từ bản đi kèm (nếu chạy từ repo đã tải) hoặc mặc định
$LK = $null
$lkFile = Join-Path $PSScriptRoot "lien-ket.json"
if ($PSScriptRoot -and (Test-Path $lkFile)) { $LK = Get-Content $lkFile -Raw -Encoding UTF8 | ConvertFrom-Json }
$REPO = if ($LK) { $LK.skill_repo } else { "https://github.com/phamthilyntnd-sketch/edit-capcut-AI.git" }
$U2NET_URL = if ($LK) { $LK.mo_hinh.u2net_human_seg.url } else { "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx" }
if (-not $ThuMuc) { $ThuMuc = Join-Path $env:USERPROFILE ".claude\skills\edit-capcut-ai" }

function CaiWinget($id, $ten) {
    if ($KiemTra) { Canh "Thiếu $ten (chế độ kiểm: không cài)"; return }
    if (-not (CoLenh winget)) { throw "Máy không có winget (App Installer). Cài 'App Installer' từ Microsoft Store rồi chạy lại." }
    Write-Host "   Đang cài $ten ($id)..."
    winget install -e --id $id --silent --accept-package-agreements --accept-source-agreements | Out-Host
    LamMoiPath
}

Buoc "1. Phần mềm nền"
# Claude (app desktop có tab Code) hoặc Claude Code dòng lệnh — skill chạy trong đó
$coClaude = (CoLenh claude) -or [bool](Get-AppxPackage -Name "*Claude*" -ErrorAction SilentlyContinue) -or (Test-Path "$env:LOCALAPPDATA\AnthropicClaude")
if ($coClaude) { Ok "Claude (desktop / Claude Code)" } else {
    $claudeId = if ($LK -and $LK.winget.claude) { $LK.winget.claude } else { "Anthropic.Claude" }
    CaiWinget $claudeId "Claude desktop (có tab Code)"
    if (-not $KiemTra) { Canh "Mở app Claude, đăng nhập tài khoản công ty, rồi vào tab Code" }
}
if (CoLenh git) { Ok "Git" } else { CaiWinget "Git.Git" "Git" }
$py = $null
foreach ($c in @("py", "python")) { if (CoLenh $c) { $py = $c; break } }
if ($py) { Ok "Python ($py)" } else { CaiWinget "Python.Python.3.12" "Python 3.12"; $py = "py" }
if (CoLenh node) { Ok "Node.js" } else { CaiWinget "OpenJS.NodeJS.LTS" "Node.js" }
if (CoLenh ffmpeg) { Ok "ffmpeg" } else { CaiWinget "Gyan.FFmpeg" "ffmpeg" }
$coChrome = (Test-Path "$env:ProgramFiles\Google\Chrome\Application\chrome.exe") -or (Test-Path "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe") -or (Test-Path "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe")
if ($coChrome) { Ok "Chrome/Edge" } else { CaiWinget "Google.Chrome" "Google Chrome" }
$capcutDrafts = Join-Path $env:LOCALAPPDATA "CapCut\User Data\Projects\com.lveditor.draft"
if (Test-Path $capcutDrafts) { Ok "CapCut desktop" } elseif ($KiemTra) { Canh "Chưa có CapCut desktop" } else {
    CaiWinget "ByteDance.CapCut" "CapCut desktop"
    # mở CapCut 1 lần để nó tạo thư mục project (không tự tắt — người dùng tự đóng)
    $ccApp = Get-StartApps | Where-Object { $_.Name -eq "CapCut" } | Select-Object -First 1
    if ($ccApp) { Start-Process "explorer.exe" "shell:AppsFolder\$($ccApp.AppID)" }
    Write-Host "   Đang chờ CapCut mở lần đầu (tối đa 2 phút)..."
    for ($i = 0; $i -lt 60 -and -not (Test-Path $capcutDrafts); $i++) { Start-Sleep 2 }
    if (Test-Path $capcutDrafts) { Ok "CapCut desktop (đã mở lần đầu — đăng nhập/đóng tuỳ bạn)" }
    else { Canh "CapCut chưa tạo thư mục project: mở CapCut, tạo 1 project trống, đóng, rồi chạy lại bộ cài"; Start-Process "https://www.capcut.com/download" }
}

Buoc "2. Skill từ GitHub -> $ThuMuc"
if ($KiemTra) {
    if (Test-Path (Join-Path $ThuMuc "SKILL.md")) { Ok "Đã có skill" } else { Canh "Chưa có skill" }
} elseif (Test-Path (Join-Path $ThuMuc ".git")) {
    git -C $ThuMuc pull --ff-only | Out-Host; Ok "Đã cập nhật bản mới nhất"
} else {
    New-Item -ItemType Directory -Force (Split-Path $ThuMuc) | Out-Null
    Write-Host "   (repo riêng tư: nếu hiện cửa sổ đăng nhập GitHub, đăng nhập bằng tài khoản đã được mời vào repo)"
    git clone $REPO $ThuMuc | Out-Host; Ok "Đã tải skill"
}
if (-not (Test-Path (Join-Path $ThuMuc "SKILL.md"))) { if ($KiemTra) { exit 1 } else { throw "Không tải được skill" } }

Buoc "3. Thư viện Python (môi trường riêng .venv)"
$venvPy = Join-Path $ThuMuc ".venv\Scripts\python.exe"
if (-not $KiemTra) {
    if (-not (Test-Path $venvPy)) {
        if ($py -eq "py") { & py -3 -m venv (Join-Path $ThuMuc ".venv") } else { & python -m venv (Join-Path $ThuMuc ".venv") }
    }
    & $venvPy -m pip install --upgrade pip -q
    & $venvPy -m pip install -r (Join-Path $ThuMuc "requirements.txt") -q
}
if (Test-Path $venvPy) { Ok "Python của skill: $venvPy" } else { Canh "Chưa có .venv" }

Buoc "4. capcut-cli"
if (CoLenh capcut) { Ok "capcut-cli" } elseif (-not $KiemTra) { npm i -g capcut-cli | Out-Host; LamMoiPath; Ok "Đã cài capcut-cli" } else { Canh "Thiếu capcut-cli" }

Buoc "5. Mô hình (tải sẵn)"
$models = Join-Path $ThuMuc "models"
$u2 = Join-Path $models "u2net_human_seg.onnx"
if (Test-Path $u2) { Ok "u2net_human_seg.onnx" } elseif (-not $KiemTra) {
    New-Item -ItemType Directory -Force $models | Out-Null
    Write-Host "   Đang tải mô hình tách người (~170 MB)..."
    $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest -Uri $U2NET_URL -OutFile $u2 -UseBasicParsing
    Ok "Đã tải u2net_human_seg.onnx"
} else { Canh "Thiếu u2net_human_seg.onnx" }
# may.json: ghi đường dẫn mô hình (giữ các khoá người dùng đã sửa)
$mayFile = Join-Path $ThuMuc "may.json"
$may = @{}
if (Test-Path $mayFile) { (Get-Content $mayFile -Raw -Encoding UTF8 | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $may[$_.Name] = $_.Value } }
if ((Test-Path $u2) -and -not $may["u2net"]) { $may["u2net"] = $u2 }
if (-not $KiemTra) { ($may | ConvertTo-Json) | Set-Content -Path $mayFile -Encoding UTF8 }
if ((Test-Path $venvPy) -and -not $KiemTra) {
    Write-Host "   Đang tải mô hình nghe tiếng Việt Whisper large-v3-turbo (~1,6 GB, chỉ lần đầu)..."
    & $venvPy -c "from faster_whisper import WhisperModel; WhisperModel('large-v3-turbo', device='cpu', compute_type='int8'); print('   [OK] Whisper large-v3-turbo')"
}

Buoc "6. Bộ tiếng nhấn + kiểm máy"
if (Test-Path $venvPy) {
    if (-not $KiemTra) { & $venvPy -I (Join-Path $ThuMuc "scripts\tao_sfx.py") }
    & $venvPy -I (Join-Path $ThuMuc "scripts\kiem_may.py")
    $kq = $LASTEXITCODE
} else { $kq = 1 }
Buoc "7. Lối tắt cập nhật trên Desktop"
$cmdFile = Join-Path $ThuMuc "cai-dat\CAI-DAT.cmd"
if (-not $KiemTra -and (Test-Path $cmdFile)) {
    try {
        $lnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "Cap nhat skill edit-capcut-AI.lnk"
        $ws = New-Object -ComObject WScript.Shell
        $sc = $ws.CreateShortcut($lnk); $sc.TargetPath = $cmdFile; $sc.WorkingDirectory = $ThuMuc; $sc.Save()
        Ok "Desktop: 'Cap nhat skill edit-capcut-AI' (bấm đúp khi có bản mới)"
    } catch { Canh "Không tạo được lối tắt (không ảnh hưởng)" }
}

Buoc "8. Chuẩn bị EDIT THỬ"
$lam = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "Edit-CapCut-AI"
$thu = Join-Path $lam "footage\video-thu"
$cau = "Dựng video trong thư mục `"$thu`" cho thương hiệu santav thành project CapCut. Đây là video edit thử."
if (-not $KiemTra) {
    New-Item -ItemType Directory -Force $thu | Out-Null
    $hd = @"
EDIT THỬ VIDEO ĐẦU TIÊN — 3 bước
=================================
1. Chép vào thư mục footage\video-thu (ngay cạnh file này):
   - 1 clip người nói (quay dọc, nói hết kịch bản)
   - vài clip cảnh trám sản phẩm (mỗi clip từ 5 giây)
2. Mở app AI (Claude) -> tab Code -> chọn thư mục làm việc:
   $lam
3. Dán câu dưới (đã chép sẵn vào bộ nhớ, chỉ cần Ctrl+V) rồi Enter:

   $cau

AI hỏi những gì còn thiếu 1 lần, rồi tự dựng tới xong. Khi AI nhắc "đóng CapCut" thì tắt hẳn CapCut.
Khách khác: đổi "santav" thành tên hồ sơ thương hiệu của khách.
"@
    Set-Content -Path (Join-Path $lam "BAT-DAU-EDIT-THU.txt") -Value $hd -Encoding UTF8
    try { Set-Clipboard -Value $cau } catch {}
    Ok "Thư mục làm việc: $lam (bỏ footage vào footage\video-thu)"
}

Write-Host ""
if ($kq -eq 0) {
    Write-Host "XONG. TẮT HẲN rồi MỞ LẠI app AI (Claude) để nhận skill." -ForegroundColor Green
    Write-Host "EDIT THỬ: bỏ footage vào $thu, mở app AI -> tab Code -> chọn thư mục $lam, dán câu (đã chép sẵn, Ctrl+V):" -ForegroundColor Green
    Write-Host "   $cau" -ForegroundColor Green
    if (-not $KiemTra) {
        Start-Process "explorer.exe" "`"$lam`""
        Start-Process "notepad.exe" "`"$(Join-Path $lam 'BAT-DAU-EDIT-THU.txt')`""
        $claudeApp = Get-StartApps | Where-Object { $_.Name -eq "Claude" } | Select-Object -First 1
        if ($claudeApp) { Start-Process "explorer.exe" "shell:AppsFolder\$($claudeApp.AppID)" }
    }
} else {
    Write-Host "Còn thiếu mục bắt buộc ở trên — sửa theo gợi ý rồi chạy lại bộ cài." -ForegroundColor Yellow
}
exit $kq
