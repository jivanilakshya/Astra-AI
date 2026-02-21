@echo off
REM Windows installation script for LangChain migration

echo ====================================================================
echo  Installing LangChain/LangGraph Dependencies
echo ====================================================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python first.
    exit /b 1
)

echo.
echo Installing packages from requirements_langchain.txt...
echo.

pip install -r requirements_langchain.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Installation failed!
    exit /b 1
)

echo.
echo ====================================================================
echo  Installation Complete!
echo ====================================================================
echo.
echo Next steps:
echo   1. Configure LangSmith (optional):
echo      - Get API key: https://smith.langchain.com
echo      - Add to .env: LANGCHAIN_API_KEY=your_key_here
echo.
echo   2. Run test:
echo      python test_langchain_migration.py
echo.
echo   3. Run full system:
echo      python main_langchain.py --interactive
echo.
echo ====================================================================

pause
