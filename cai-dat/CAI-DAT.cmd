@echo off
chcp 65001 >nul
rem ================================================================
rem  CAI DAT SKILL edit-capcut-AI - bam dup file nay la xong.
rem  Repo RIENG TU: tai khoan GitHub cua ban phai duoc quan ly moi
rem  va ban da bam "Accept invitation" trong email truoc khi chay.
rem  Tu cai Git (neu thieu), dang nhap GitHub, tai skill, roi chay bo cai
rem  day du (Claude, Python, Node.js, ffmpeg, capcut-cli, mo hinh, kiem may).
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

if exist "%DICH%\.git" goto CAPNHAT

echo.
echo == Tai skill tu GitHub (repo rieng tu)
echo    Neu hien cua so dang nhap GitHub: chon "Sign in with your browser"
echo    va dang nhap DUNG tai khoan da duoc moi vao repo.
git clone "%REPO%" "%DICH%"
if exist "%DICH%\cai-dat\cai-dat.ps1" goto CAI
goto DANGNHAP

:CAPNHAT
echo == Cap nhat skill...
git -C "%DICH%" pull --ff-only
if errorlevel 1 goto DANGNHAP
goto CAI

:DANGNHAP
echo.
echo == Chua vao duoc repo. Dang nhap GitHub bang MA:
echo    1. Mo trinh duyet: https://github.com/login/device  (dang nhap tai khoan da duoc moi)
echo    2. Nhap MA hien ben duoi, bam Continue roi Authorize, roi quay lai cua so nay.
echo.
git credential-manager github login --device --no-ui
if exist "%DICH%\.git" (
  git -C "%DICH%" pull --ff-only
) else (
  git clone "%REPO%" "%DICH%"
)
if exist "%DICH%\cai-dat\cai-dat.ps1" goto CAI
echo.
echo [LOI] Van khong tai duoc skill. Kiem tra:
echo   - May co mang khong?
echo   - Tai khoan GitHub da duoc QUAN LY MOI vao repo va ban da bam "Accept invitation" trong email chua?
echo   - Ban dang nhap DUNG tai khoan do chua?
echo Xong roi bam dup lai file nay. Van loi: chup man hinh gui quan ly.
pause
exit /b 1

:CAI
powershell -NoProfile -ExecutionPolicy Bypass -File "%DICH%\cai-dat\cai-dat.ps1" -ThuMuc "%DICH%"
echo.
pause
