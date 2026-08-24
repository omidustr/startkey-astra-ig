@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo ================================================
echo  Startkey Astra Instagram Otomasyonu - GitHub yukleme
echo ================================================
echo.
git --version >nul 2>&1
if errorlevel 1 (
  echo HATA: Git kurulu degil.
  echo https://git-scm.com/download/win adresinden kurup tekrar deneyin.
  pause
  exit /b 1
)
echo Once github.com adresinde HERKESE ACIK ^(public^) bos bir depo olusturun.
echo Sonra adresini asagiya yapistirin.
echo.
set /p REPO="Depo adresi (ornek https://github.com/kullanici/startkey-astra-ig.git): "
if "%REPO%"=="" (echo Adres girilmedi. & pause & exit /b 1)
if exist .git rmdir /s /q .git
git init -b main
git add -A
git -c user.name="Olcay" -c user.email="zobekci@gmail.com" commit -m "Startkey Astra Instagram otomasyonu"
git remote add origin %REPO%
echo.
echo Yukleniyor... GitHub girisi icin tarayici acilirsa onaylayin.
git push -u origin main
if errorlevel 1 (echo. & echo Yukleme basarisiz. Hata mesajini Claude'a gosterin. & pause & exit /b 1)
echo.
echo ================================================
echo  Yuklendi. Simdi README.md icindeki kurulum adimlarini takip edin.
echo ================================================
pause
