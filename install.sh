#!/usr/bin/env bash
# install.sh – macOS / Linux quick-start installer for Resume Optimizer Pro
#
# Usage:
#   chmod +x install.sh
#   ./install.sh

set -euo pipefail

echo "============================================"
echo "   Resume Optimizer Pro  –  Installer"
echo "============================================"
echo ""

# ── Python version check ─────────────────────────────────────────────────────
PYTHON=$(command -v python3 || true)
if [[ -z "$PYTHON" ]]; then
  echo "ERROR: python3 not found."
  echo "macOS: brew install python   (or download from python.org)"
  exit 1
fi

PY_VER=$("$PYTHON" -c "import sys; print('%d.%d' % sys.version_info[:2])")
PY_MAJOR=$("$PYTHON" -c "import sys; print(sys.version_info[0])")
PY_MINOR=$("$PYTHON" -c "import sys; print(sys.version_info[1])")

if [[ "$PY_MAJOR" -lt 3 || ("$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 9) ]]; then
  echo "ERROR: Python 3.9+ required (found $PY_VER)"
  echo "macOS: brew upgrade python   (or re-install from python.org)"
  exit 1
fi
echo "✅  Python $PY_VER found"

# ── tkinter check ────────────────────────────────────────────────────────────
if ! "$PYTHON" -c "import tkinter" 2>/dev/null; then
  echo ""
  echo "⚠️  tkinter is not installed."
  if [[ "$(uname)" == "Darwin" ]]; then
    echo "    Run:  brew install python-tk@${PY_VER%.*}"
    echo "    or reinstall Python from https://www.python.org/downloads/"
  else
    echo "    Run:  sudo apt install python3-tk  (Debian/Ubuntu)"
    echo "          sudo dnf install python3-tkinter  (Fedora/RHEL)"
  fi
  echo ""
  echo "    After installing tkinter, re-run this script."
  exit 1
fi
echo "✅  tkinter found"

# ── Create virtual environment ───────────────────────────────────────────────
VENV_DIR="venv"
if [[ ! -d "$VENV_DIR" ]]; then
  echo ""
  echo "Creating virtual environment in ./$VENV_DIR …"
  "$PYTHON" -m venv "$VENV_DIR"
fi

# Activate venv
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
echo "✅  Virtual environment activated"

# ── Install dependencies ─────────────────────────────────────────────────────
echo ""
echo "Installing Python dependencies …"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "✅  Dependencies installed"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "============================================"
echo "  Installation complete! 🎉"
echo "============================================"
echo ""
echo "  To launch the app:"
echo "    source venv/bin/activate"
echo "    python main.py"
echo ""
echo "  Or simply run:  ./run.sh"
echo ""

# Create convenience run script
cat > run.sh << 'EOF'
#!/usr/bin/env bash
# run.sh – Launch Resume Optimizer Pro
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source venv/bin/activate
python main.py "$@"
EOF
chmod +x run.sh
echo "  Created run.sh for easy launching."
echo ""
