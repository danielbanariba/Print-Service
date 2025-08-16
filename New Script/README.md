# 1. Compilar el ejecutable

``` shell
pyinstaller --onefile --hidden-import=servicemanager --hidden-import=win32timezone --hidden-import=win32print --hidden-import=win32service --hidden-import=win32serviceutil --hidden-import=pywintypes --hidden-import=win32event TSSPrint_2025.py
```

# 2. El ejecutable se generará en: dist\TSSPrint_2025.exe
