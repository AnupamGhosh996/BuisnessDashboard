param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)
$env:PYTHONHOME = "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0"
$env:PYTHONPATH = "$PSScriptRoot\backend\runtime\DLLs;$PSScriptRoot\backend"
& "$PSScriptRoot\backend\runtime\python.exe" @Args
