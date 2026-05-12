#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/render_queue.log"
VENV_DIR="$SCRIPT_DIR/venvDigger"

mkdir -p "$LOG_DIR"

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

log "Starting queued video render."

cd "$SCRIPT_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
    log "Virtual environment not found at $VENV_DIR"
    log "Expected setup: source venvDigger/bin/activate && python render_queue.py"
    exit 1
fi

source "$VENV_DIR/bin/activate"

log "Using Python: $(command -v python)"
log "Rendering queued stories from data/queue."

python render_queue.py 2>&1 | tee -a "$LOG_FILE"
status=${PIPESTATUS[0]}

deactivate || true

if [[ "$status" -eq 0 ]]; then
    log "Queued video render completed successfully."
else
    log "Queued video render finished with failures. Check data/queue/failed and $LOG_FILE."
fi

exit "$status"
