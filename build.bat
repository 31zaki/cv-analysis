@echo off
echo ============================================
echo   CV Analysis Suite - PyInstaller Build
echo ============================================

:: Install/upgrade dependencies
python -m pip install -r requirements.txt --quiet

:: Run PyInstaller
pyinstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name "CV Analysis Suite" ^
  --add-data "src;src" ^
  main.py

echo.
if exist "dist\CV Analysis Suite.exe" (
    echo Build complete: dist\CV Analysis Suite.exe
) else (
    echo Build may have failed - check output above.
)
pause
