# Windows nmake Makefile for PyCon 2025 FFI Experiments
# Based on official CPython PCbuild/readme.txt
# Mirrors GNUmakefile behavior using Windows-native tools

# Python versions to build
PYTHON_313_VERSION = 3.13.5
PYTHON_314_VERSION = 3.14.0rc1

# Build directories (Windows style)
BUILD_DIR = build
CACHE_DIR = $(BUILD_DIR)\cache
PYTHON_313_SRC = $(BUILD_DIR)\Python-$(PYTHON_313_VERSION)
PYTHON_314_SRC = $(BUILD_DIR)\Python-$(PYTHON_314_VERSION)

# Installation prefixes (Windows style)
PYTHON_313_NOGIL_PREFIX = $(MAKEDIR)\cpython3.13.5-nogil
PYTHON_314_NOGIL_PREFIX = $(MAKEDIR)\cpython3.14.0rc1-nogil
PYTHON_313_GIL_PREFIX = $(MAKEDIR)\cpython3.13.5-gil
PYTHON_314_GIL_PREFIX = $(MAKEDIR)\cpython3.14.0rc1-gil

# Python source URLs
PYTHON_313_URL = https://www.python.org/ftp/python/$(PYTHON_313_VERSION)/Python-$(PYTHON_313_VERSION).tgz
PYTHON_314_URL = https://www.python.org/ftp/python/3.14.0/Python-$(PYTHON_314_VERSION).tgz

# Build configuration (following official CPython Windows build)
PLATFORM = x64
CONFIG = Release

# Number of parallel jobs (Windows equivalent)
!IF "$(NUMBER_OF_PROCESSORS)" != ""
JOBS = $(NUMBER_OF_PROCESSORS)
!ELSE
JOBS = 4
!ENDIF

# Main targets
.PHONY: all clean distclean test help
.PHONY: python-313-nogil python-314-nogil python-313-gil python-314-gil
.PHONY: 313-nogil 314-nogil 313-gil 314-gil 313 314

all: python-313-nogil python-314-nogil python-313-gil python-314-gil

help:
	@echo Windows CPython Build System for PyCon 2025 FFI Experiments
	@echo Based on official PCbuild methodology
	@echo.
	@echo Available targets:
	@echo   all                 - Build all Python versions
	@echo   python-313-nogil    - Build Python 3.13.5 with --disable-gil
	@echo   python-314-nogil    - Build Python 3.14.0rc1 with --disable-gil
	@echo   python-313-gil      - Build Python 3.13.5 standard
	@echo   python-314-gil      - Build Python 3.14.0rc1 standard
	@echo   test               - Test all installations
	@echo   clean              - Clean build artifacts
	@echo   distclean          - Clean everything including downloads
	@echo.
	@echo Shortcuts:
	@echo   313-nogil, 314-nogil, 313-gil, 314-gil
	@echo   313 (both GIL variants), 314 (both GIL variants)
	@echo.
	@echo Note: --disable-gil now supported on Windows (experimental)

# Create directories
$(BUILD_DIR):
	@if not exist "$@" mkdir "$@"

$(CACHE_DIR): $(BUILD_DIR)
	@if not exist "$@" mkdir "$@"

# Download Python source archives (Windows curl)
$(CACHE_DIR)\Python-$(PYTHON_313_VERSION).tgz: $(CACHE_DIR)
	@echo Downloading Python $(PYTHON_313_VERSION)...
	@curl -L -o "$@" "$(PYTHON_313_URL)"

$(CACHE_DIR)\Python-$(PYTHON_314_VERSION).tgz: $(CACHE_DIR)
	@echo Downloading Python $(PYTHON_314_VERSION)...
	@curl -L -o "$@" "$(PYTHON_314_URL)"

# Extract Python source (Windows tar)
$(PYTHON_313_SRC): $(CACHE_DIR)\Python-$(PYTHON_313_VERSION).tgz $(BUILD_DIR)
	@echo Extracting Python $(PYTHON_313_VERSION)...
	@cd $(BUILD_DIR) && tar -xzf "cache\Python-$(PYTHON_313_VERSION).tgz"
	@if not exist "$@" echo Extraction verification failed && exit /b 1

$(PYTHON_314_SRC): $(CACHE_DIR)\Python-$(PYTHON_314_VERSION).tgz $(BUILD_DIR)
	@echo Extracting Python $(PYTHON_314_VERSION)...
	@cd $(BUILD_DIR) && tar -xzf "cache\Python-$(PYTHON_314_VERSION).tgz"
	@if not exist "$@" echo Extraction verification failed && exit /b 1

# Build Python 3.13 with --disable-gil (Windows adaptation)
python-313-nogil: $(PYTHON_313_SRC)
	@echo.
	@echo =====================================
	@echo Building Python $(PYTHON_313_VERSION) for Windows
	@echo =====================================
	@echo.
	@echo Using official Windows --disable-gil support
	@echo Building true no-GIL Python for FFI experiments
	@echo.
	@echo Getting external dependencies...
	@cd "$(PYTHON_313_SRC)\PCbuild" && get_externals.bat
	@echo.
	@echo Building Python $(PYTHON_313_VERSION) with --disable-gil ($(PLATFORM) $(CONFIG))...
	@cd "$(PYTHON_313_SRC)\PCbuild" && build.bat --disable-gil -p $(PLATFORM) -c $(CONFIG)
	@echo.
	@echo Installing to $(PYTHON_313_NOGIL_PREFIX)...
	@if not exist "$(PYTHON_313_NOGIL_PREFIX)" mkdir "$(PYTHON_313_NOGIL_PREFIX)"
	@if not exist "$(PYTHON_313_NOGIL_PREFIX)\bin" mkdir "$(PYTHON_313_NOGIL_PREFIX)\bin"
	@if not exist "$(PYTHON_313_NOGIL_PREFIX)\lib" mkdir "$(PYTHON_313_NOGIL_PREFIX)\lib"
	@if not exist "$(PYTHON_313_NOGIL_PREFIX)\include" mkdir "$(PYTHON_313_NOGIL_PREFIX)\include"
	@copy "$(PYTHON_313_SRC)\PCbuild\amd64\python*.exe" "$(PYTHON_313_NOGIL_PREFIX)\bin\" >nul
	@copy "$(PYTHON_313_SRC)\PCbuild\amd64\python*.dll" "$(PYTHON_313_NOGIL_PREFIX)\bin\" >nul
	@copy "$(PYTHON_313_SRC)\PCbuild\amd64\*.pyd" "$(PYTHON_313_NOGIL_PREFIX)\lib\" >nul
	@xcopy "$(PYTHON_313_SRC)\Lib\*" "$(PYTHON_313_NOGIL_PREFIX)\lib\" /E /I /Y /Q >nul
	@xcopy "$(PYTHON_313_SRC)\Include\*" "$(PYTHON_313_NOGIL_PREFIX)\include\" /E /I /Y /Q >nul
	@echo.
	@echo ✓ Python 3.13 (no-GIL) installed at: $(PYTHON_313_NOGIL_PREFIX)

# Build Python 3.14 with --disable-gil
python-314-nogil: $(PYTHON_314_SRC)
	@echo.
	@echo =====================================
	@echo Building Python $(PYTHON_314_VERSION) for Windows
	@echo =====================================
	@echo.
	@echo Using official Windows --disable-gil support
	@echo Building true no-GIL Python for FFI experiments
	@echo.
	@echo Getting external dependencies...
	@cd "$(PYTHON_314_SRC)\PCbuild" && get_externals.bat
	@echo.
	@echo Building Python $(PYTHON_314_VERSION) with --disable-gil ($(PLATFORM) $(CONFIG))...
	@cd "$(PYTHON_314_SRC)\PCbuild" && build.bat --disable-gil -p $(PLATFORM) -c $(CONFIG)
	@echo.
	@echo Installing to $(PYTHON_314_NOGIL_PREFIX)...
	@if not exist "$(PYTHON_314_NOGIL_PREFIX)" mkdir "$(PYTHON_314_NOGIL_PREFIX)"
	@if not exist "$(PYTHON_314_NOGIL_PREFIX)\bin" mkdir "$(PYTHON_314_NOGIL_PREFIX)\bin"
	@if not exist "$(PYTHON_314_NOGIL_PREFIX)\lib" mkdir "$(PYTHON_314_NOGIL_PREFIX)\lib"
	@if not exist "$(PYTHON_314_NOGIL_PREFIX)\include" mkdir "$(PYTHON_314_NOGIL_PREFIX)\include"
	@copy "$(PYTHON_314_SRC)\PCbuild\amd64\python*.exe" "$(PYTHON_314_NOGIL_PREFIX)\bin\" >nul
	@copy "$(PYTHON_314_SRC)\PCbuild\amd64\python*.dll" "$(PYTHON_314_NOGIL_PREFIX)\bin\" >nul
	@copy "$(PYTHON_314_SRC)\PCbuild\amd64\*.pyd" "$(PYTHON_314_NOGIL_PREFIX)\lib\" >nul
	@xcopy "$(PYTHON_314_SRC)\Lib\*" "$(PYTHON_314_NOGIL_PREFIX)\lib\" /E /I /Y /Q >nul
	@xcopy "$(PYTHON_314_SRC)\Include\*" "$(PYTHON_314_NOGIL_PREFIX)\include\" /E /I /Y /Q >nul
	@echo.
	@echo ✓ Python 3.14 (no-GIL) installed at: $(PYTHON_314_NOGIL_PREFIX)

# Build Python 3.13 with GIL (standard)
python-313-gil: $(PYTHON_313_SRC)
	@echo.
	@echo =====================================
	@echo Building Python $(PYTHON_313_VERSION) standard (with GIL)
	@echo =====================================
	@echo.
	@echo Getting external dependencies...
	@cd "$(PYTHON_313_SRC)\PCbuild" && get_externals.bat
	@echo.
	@echo Building Python $(PYTHON_313_VERSION) ($(PLATFORM) $(CONFIG))...
	@cd "$(PYTHON_313_SRC)\PCbuild" && build.bat -p $(PLATFORM) -c $(CONFIG)
	@echo.
	@echo Installing to $(PYTHON_313_GIL_PREFIX)...
	@if not exist "$(PYTHON_313_GIL_PREFIX)" mkdir "$(PYTHON_313_GIL_PREFIX)"
	@if not exist "$(PYTHON_313_GIL_PREFIX)\bin" mkdir "$(PYTHON_313_GIL_PREFIX)\bin"
	@if not exist "$(PYTHON_313_GIL_PREFIX)\lib" mkdir "$(PYTHON_313_GIL_PREFIX)\lib"
	@if not exist "$(PYTHON_313_GIL_PREFIX)\include" mkdir "$(PYTHON_313_GIL_PREFIX)\include"
	@copy "$(PYTHON_313_SRC)\PCbuild\amd64\python*.exe" "$(PYTHON_313_GIL_PREFIX)\bin\" >nul
	@copy "$(PYTHON_313_SRC)\PCbuild\amd64\python*.dll" "$(PYTHON_313_GIL_PREFIX)\bin\" >nul
	@copy "$(PYTHON_313_SRC)\PCbuild\amd64\*.pyd" "$(PYTHON_313_GIL_PREFIX)\lib\" >nul
	@xcopy "$(PYTHON_313_SRC)\Lib\*" "$(PYTHON_313_GIL_PREFIX)\lib\" /E /I /Y /Q >nul
	@xcopy "$(PYTHON_313_SRC)\Include\*" "$(PYTHON_313_GIL_PREFIX)\include\" /E /I /Y /Q >nul
	@echo.
	@echo ✓ Python 3.13 (with GIL) installed at: $(PYTHON_313_GIL_PREFIX)

# Build Python 3.14 with GIL (standard)
python-314-gil: $(PYTHON_314_SRC)
	@echo.
	@echo =====================================
	@echo Building Python $(PYTHON_314_VERSION) standard (with GIL)
	@echo =====================================
	@echo.
	@echo Getting external dependencies...
	@cd "$(PYTHON_314_SRC)\PCbuild" && get_externals.bat
	@echo.
	@echo Building Python $(PYTHON_314_VERSION) ($(PLATFORM) $(CONFIG))...
	@cd "$(PYTHON_314_SRC)\PCbuild" && build.bat -p $(PLATFORM) -c $(CONFIG)
	@echo.
	@echo Installing to $(PYTHON_314_GIL_PREFIX)...
	@if not exist "$(PYTHON_314_GIL_PREFIX)" mkdir "$(PYTHON_314_GIL_PREFIX)"
	@if not exist "$(PYTHON_314_GIL_PREFIX)\bin" mkdir "$(PYTHON_314_GIL_PREFIX)\bin"
	@if not exist "$(PYTHON_314_GIL_PREFIX)\lib" mkdir "$(PYTHON_314_GIL_PREFIX)\lib"
	@if not exist "$(PYTHON_314_GIL_PREFIX)\include" mkdir "$(PYTHON_314_GIL_PREFIX)\include"
	@copy "$(PYTHON_314_SRC)\PCbuild\amd64\python*.exe" "$(PYTHON_314_GIL_PREFIX)\bin\" >nul
	@copy "$(PYTHON_314_SRC)\PCbuild\amd64\python*.dll" "$(PYTHON_314_GIL_PREFIX)\bin\" >nul
	@copy "$(PYTHON_314_SRC)\PCbuild\amd64\*.pyd" "$(PYTHON_314_GIL_PREFIX)\lib\" >nul
	@xcopy "$(PYTHON_314_SRC)\Lib\*" "$(PYTHON_314_GIL_PREFIX)\lib\" /E /I /Y /Q >nul
	@xcopy "$(PYTHON_314_SRC)\Include\*" "$(PYTHON_314_GIL_PREFIX)\include\" /E /I /Y /Q >nul
	@echo.
	@echo ✓ Python 3.14 (with GIL) installed at: $(PYTHON_314_GIL_PREFIX)

# Test installations (mimicking GNUmakefile test target)
test:
	@echo.
	@echo =====================================
	@echo Testing Python installations
	@echo =====================================
	@echo.
	@echo === Windows Python versions ===
	@if exist "$(PYTHON_313_GIL_PREFIX)\bin\python.exe" (
		echo Python 3.13 ^(standard with GIL^):
		"$(PYTHON_313_GIL_PREFIX)\bin\python.exe" --version
		"$(PYTHON_313_GIL_PREFIX)\bin\python.exe" -c "import sys; print(f'GIL status: {\"enabled\" if not hasattr(sys, \"_is_gil_enabled\") or sys._is_gil_enabled() else \"disabled\"}')"
		"$(PYTHON_313_GIL_PREFIX)\bin\python.exe" -c "import os; print(f'add_dll_directory available: {hasattr(os, \"add_dll_directory\")}')"
		echo.
	) else (
		echo Python 3.13 ^(GIL^): Not installed
		echo.
	)
	@if exist "$(PYTHON_313_NOGIL_PREFIX)\bin\python.exe" (
		echo Python 3.13 ^(true no-GIL Windows build^):
		"$(PYTHON_313_NOGIL_PREFIX)\bin\python.exe" --version
		"$(PYTHON_313_NOGIL_PREFIX)\bin\python.exe" -c "import sys; print(f'GIL status: {\"enabled\" if not hasattr(sys, \"_is_gil_enabled\") or sys._is_gil_enabled() else \"disabled\"}')"
		"$(PYTHON_313_NOGIL_PREFIX)\bin\python.exe" -c "import os; print(f'add_dll_directory available: {hasattr(os, \"add_dll_directory\")}')"
		echo.
	) else (
		echo Python 3.13 ^(no-GIL^): Not installed
		echo.
	)
	@if exist "$(PYTHON_314_NOGIL_PREFIX)\bin\python.exe" (
		echo Python 3.14 ^(true no-GIL Windows build^):
		"$(PYTHON_314_NOGIL_PREFIX)\bin\python.exe" --version
		"$(PYTHON_314_NOGIL_PREFIX)\bin\python.exe" -c "import sys; print(f'GIL status: {\"enabled\" if not hasattr(sys, \"_is_gil_enabled\") or sys._is_gil_enabled() else \"disabled\"}')"
		"$(PYTHON_314_NOGIL_PREFIX)\bin\python.exe" -c "import os; print(f'add_dll_directory available: {hasattr(os, \"add_dll_directory\")}')"
		echo.
	) else (
		echo Python 3.14 ^(no-GIL^): Not installed
		echo.
	)
	@echo === With-GIL versions ===
	@if exist "$(PYTHON_313_GIL_PREFIX)\bin\python.exe" (
		echo Python 3.13 ^(with GIL^):
		"$(PYTHON_313_GIL_PREFIX)\bin\python.exe" --version
		"$(PYTHON_313_GIL_PREFIX)\bin\python.exe" -c "import sys; print(f'GIL enabled: not hasattr(sys, \"_is_gil_enabled\") or sys._is_gil_enabled())')"
		echo.
	) else (
		echo Python 3.13 ^(with GIL^): Not installed
		echo.
	)
	@if exist "$(PYTHON_314_GIL_PREFIX)\bin\python.exe" (
		echo Python 3.14 ^(with GIL^):
		"$(PYTHON_314_GIL_PREFIX)\bin\python.exe" --version
		"$(PYTHON_314_GIL_PREFIX)\bin\python.exe" -c "import sys; print(f'GIL enabled: not hasattr(sys, \"_is_gil_enabled\") or sys._is_gil_enabled())')"
		echo.
	) else (
		echo Python 3.14 ^(with GIL^): Not installed
		echo.
	)

# Clean build artifacts but keep downloads and installations
clean-build:
	@echo Cleaning build artifacts...
	@if exist "$(PYTHON_313_SRC)" rmdir /S /Q "$(PYTHON_313_SRC)"
	@if exist "$(PYTHON_314_SRC)" rmdir /S /Q "$(PYTHON_314_SRC)"
	@echo Clean build complete.

# Clean everything except cached downloads
clean:
	@echo Cleaning source and installations...
	@if exist "$(PYTHON_313_SRC)" rmdir /S /Q "$(PYTHON_313_SRC)"
	@if exist "$(PYTHON_314_SRC)" rmdir /S /Q "$(PYTHON_314_SRC)"
	@if exist "$(PYTHON_313_NOGIL_PREFIX)" rmdir /S /Q "$(PYTHON_313_NOGIL_PREFIX)"
	@if exist "$(PYTHON_314_NOGIL_PREFIX)" rmdir /S /Q "$(PYTHON_314_NOGIL_PREFIX)"
	@if exist "$(PYTHON_313_GIL_PREFIX)" rmdir /S /Q "$(PYTHON_313_GIL_PREFIX)"
	@if exist "$(PYTHON_314_GIL_PREFIX)" rmdir /S /Q "$(PYTHON_314_GIL_PREFIX)"
	@echo Clean complete.

# Clean everything including downloads
distclean: clean
	@echo Cleaning everything including downloads...
	@if exist "$(BUILD_DIR)" rmdir /S /Q "$(BUILD_DIR)"
	@echo Distclean complete.

# Shortcuts (mimicking GNUmakefile)
313-nogil: python-313-nogil
314-nogil: python-314-nogil
313-gil: python-313-gil
314-gil: python-314-gil
313: python-313-nogil python-313-gil
314: python-314-nogil python-314-gil