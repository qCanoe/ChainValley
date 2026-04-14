param(
  [string]$RpcUrl = "http://127.0.0.1:8545",
  [ValidateSet("0", "1")][string]$DoInit = "1",
  [ValidateSet("0", "1")][string]$HardRule = "1"
)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$env:FISHERY_DO_INIT = $DoInit
$env:FISHERY_HARD_RULE = $HardRule
$env:ETH_RPC_URL = $RpcUrl

# Git Bash / profile often adds ~/.foundry/bin; PowerShell started from IDE/conda may not have it.
$foundryBins = @(
  (Join-Path $env:USERPROFILE ".foundry\bin"),
  (Join-Path $env:LOCALAPPDATA "foundry\bin")
)
foreach ($dir in $foundryBins) {
  if (Test-Path -LiteralPath $dir) {
    $env:PATH = "$dir;$env:PATH"
  }
}

pnpm --filter contracts run deploy:local
# Propagate pnpm/mud exit code so callers (e.g. Python subprocess.check=True) fail on deploy errors.
exit $LASTEXITCODE
