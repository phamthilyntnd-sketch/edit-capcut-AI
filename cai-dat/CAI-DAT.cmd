@echo off
chcp 65001 >nul
rem ================================================================
rem  CAI DAT SKILL edit-capcut-AI - bam dup file nay la xong.
rem  Tu cai Git (neu thieu), tai skill tu GitHub, roi chay bo cai day du
rem  (Python, Node.js, ffmpeg, capcut-cli, mo hinh, tieng nhan, kiem may).
rem  Chay lai bat cu luc nao de CAP NHAT skill.
rem ================================================================
set "REPO=https://github.com/phamthilyntnd-sketch/edit-capcut-AI.git"
set "DICH=%USERPROFILE%\.claude\skills\edit-capcut-ai"

where git >nul 2>nul
if errorlevel 1 (
  echo == Chua co Git - dang cai...
  winget install -e --id Git.Git --silent --accept-package-agreements --accept-source-agreements
  set "PATH=%PATH%;%ProgramFiles%\Git\cmd"
)

if exist "%DICH%\.git" (
  echo == Cap nhat skill...
  git -C "%DICH%" pull --ff-only
) else (
  echo == Tai skill tu GitHub (repo rieng tu: neu hien cua so dang nhap GitHub, dang nhap tai khoan da duoc moi)...
  git clone "%REPO%" "%DICH%"
)
if not exist "%DICH%\cai-dat\cai-dat.ps1" (
  echo [LOI] Khong tai duoc skill. Kiem tra mang / quyen truy cap repo roi chay lai.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%DICH%\cai-dat\cai-dat.ps1" -ThuMuc "%DICH%"
echo.
pause
