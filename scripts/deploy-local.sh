#!/usr/bin/env bash
set -euo pipefail
RPC_URL="${1:-http://127.0.0.1:8545}"
export FISHERY_DO_INIT="${FISHERY_DO_INIT:-1}"
export FISHERY_HARD_RULE="${FISHERY_HARD_RULE:-1}"
export ETH_RPC_URL="$RPC_URL"
cd "$(dirname "$0")/.."
pnpm --filter contracts run deploy:local
