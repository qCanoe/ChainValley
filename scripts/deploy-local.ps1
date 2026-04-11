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
pnpm --filter contracts run deploy:local
