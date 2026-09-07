$ErrorActionPreference = "Continue"
& .\.venv_verify\Scripts\python.exe scripts\measure_performance.py > perf_output.log 2>&1
Write-Host "Performance measurement complete. Check perf_output.log for results."
