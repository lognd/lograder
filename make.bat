@echo off
setlocal enabledelayedexpansion

set VENV_DIR=.venv
set VENV_PYTHON=%VENV_DIR%\Scripts\python.exe
set VENV_PIP=%VENV_DIR%\Scripts\pip.exe
set VENV_PYTEST=%VENV_DIR%\Scripts\pytest.exe
set VENV_MYPY=%VENV_DIR%\Scripts\mypy.exe
set VENV_BLACK=%VENV_DIR%\Scripts\black.exe
set VENV_RUFF=%VENV_DIR%\Scripts\ruff.exe
set VENV_ISORT=%VENV_DIR%\Scripts\isort.exe

:: Entry point
if "%1"=="" (
    call :venv
    call :build
    call :check
    call :test
    goto :eof
)
call :%1
goto :eof

:venv
echo Creating virtual environment in %VENV_DIR%...
if not exist "%VENV_PYTHON%" (
    python -m venv %VENV_DIR%
)
call %VENV_PYTHON% -m pip install --upgrade pip
call %VENV_PIP% install --upgrade setuptools
goto :eof

:build
call :clean
call :preinstall
call :uninstall
call :reinstall
goto :eof

:preinstall
echo Installing pre-install dependencies
:: call %VENV_PIP% install --upgrade pip setuptools
echo Running pre-install scripts...
goto :eof

:uninstall
echo Uninstalling lograder...
call %VENV_PIP% uninstall -y lograder || echo (Already uninstalled)
goto :eof

:reinstall
echo Installing lograder in editable mode with test extras...
call %VENV_PIP% install -e .[dev]
goto :eof

:test
echo Running tests...
call %VENV_PYTEST% tests/ -q --tb=short --maxfail=5
goto :eof

:type
echo Type-checking with mypy...
call %VENV_MYPY% src
goto :eof

:lint
echo Linting the code...
call %VENV_RUFF% check --fix src tests
goto :eof

:format
echo Checking format with black...
call %VENV_BLACK% src tests
goto :eof

:imports
echo Checking import order with isort...
call %VENV_ISORT% src tests
goto :eof

:check
call :imports
call :lint
call :type
call :format
call :test
goto :eof

:clean
echo Cleaning build artifacts...

:: Delete known build folders
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d %%D in (*.egg-info) do rmdir /s /q "%%D"
if exist .pytest_cache rmdir /s /q .pytest_cache

:: Remove all __pycache__ folders recursively
powershell -Command "Get-ChildItem -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force"
:: Remove all *.so and *.pyd files recursively in src/
powershell -Command "Get-ChildItem -Path src -Include *.so,*.pyd -Recurse | Remove-Item -Force"

goto :eof