@echo off
REM LangSmith Configuration Helper

echo ====================================================================
echo  LangSmith Setup for Astra AI
echo ====================================================================
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env first.
    pause
    exit /b 1
)

echo Current LangSmith Configuration:
echo --------------------------------
type .env | findstr LANGCHAIN
echo.
echo ====================================================================
echo.

echo To enable LangSmith tracing:
echo.
echo 1. Go to: https://smith.langchain.com
echo 2. Sign up for free account
echo 3. Go to Settings -^> API Keys
echo 4. Create new API key (starts with lsv2_...)
echo 5. Copy the key
echo.
echo 6. Open .env file and replace:
echo    LANGCHAIN_API_KEY=your_langsmith_api_key_here
echo.
echo    With your actual key:
echo    LANGCHAIN_API_KEY=lsv2_pt_xxxxxxxxxxxxx...
echo.
echo 7. Save .env file
echo.
echo ====================================================================
echo.

echo To test LangSmith after setup:
echo.
echo   python test_judge.py
echo.
echo Then check traces at: https://smith.langchain.com
echo   -^> Project: astra-ai-judge
echo.
echo ====================================================================
echo.

pause
