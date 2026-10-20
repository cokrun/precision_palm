<#
.Synopsis
Activates a Python virtual environment in Windows PowerShell.
#>

$script:THIS_PATH = $myinvocation.mycommand.path
$script:BASE_DIR = Split-Path (Split-Path $script:THIS_PATH -Parent) -Parent

function global:deactivate ([switch]$NonDestructive) {
    if (Test-Path variable:_OLD_VIRTUAL_PATH) {
        $env:PATH = $variable:_OLD_VIRTUAL_PATH
        Remove-Variable "_OLD_VIRTUAL_PATH" -Scope global
    }
    if (Test-Path variable:_OLD_VIRTUAL_PROMPT) {
        $function:prompt = $variable:_OLD_VIRTUAL_PROMPT
        Remove-Variable "_OLD_VIRTUAL_PROMPT" -Scope global
    }
    Remove-Variable "VIRTUAL_ENV" -Scope global -ErrorAction SilentlyContinue
    if (-not $NonDestructive) {
        Remove-Item function:deactivate -ErrorAction SilentlyContinue
    }
}

deactivate -NonDestructive

$env:VIRTUAL_ENV = $script:BASE_DIR
$global:_OLD_VIRTUAL_PATH = $env:PATH
$env:PATH = "$script:BASE_DIR\Scripts;" + $env:PATH

if (-not $env:VIRTUAL_ENV_DISABLE_PROMPT) {
    $global:_OLD_VIRTUAL_PROMPT = $function:prompt
    function global:prompt {
        Write-Host "($(Split-Path $env:VIRTUAL_ENV -Leaf)) " -NoNewline -ForegroundColor Green
        & $global:_OLD_VIRTUAL_PROMPT
    }
}