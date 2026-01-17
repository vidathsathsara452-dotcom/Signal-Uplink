#!/usr/bin/env bash

set -e

INSTALL_DIR="/usr/share/SignalUplink"
BIN_PATH="/usr/local/bin/signaluplink"
BANNER_FILE="$INSTALL_DIR/banner.txt"

echo "[*] Installing SignalUplink..."

# Require root
if [[ "$EUID" -ne 0 ]]; then
  echo "[-] Please run as root"
  exit 1
fi

# Create install directory
mkdir -p "$INSTALL_DIR"

# Copy files
cp SignalUplink.py "$INSTALL_DIR/"
cp banner.txt "$INSTALL_DIR/"

# Make executable
chmod +x "$INSTALL_DIR/SignalUplink.py"

# Create launcher
ln -sf "$INSTALL_DIR/SignalUplink.py" "$BIN_PATH"

# -------------------------------
# Show banner & ask for edit
# -------------------------------
echo
echo "================ CURRENT BANNER ================"
cat "$BANNER_FILE"
echo "================================================"
echo

read -rp "Do you want to edit the banner? (y/N): " EDIT_BANNER

if [[ "$EDIT_BANNER" =~ ^[Yy]$ ]]; then
    echo
    echo "[*] ASCII Banner Generator Sites:"
    echo "  - https://patorjk.com/software/taag/"
    echo "  - https://manytools.org/hacker-tools/ascii-banner/"
    echo "  - https://textkool.com/en/ascii-art-generator"
    echo "  - https://www.asciiart.eu/text-to-ascii-art"
    echo
    echo "[*] Paste your new banner into the editor."
    echo "[*] One line per row. Padding remains fixed (8)."
    echo

    # Open editor
    if [[ -n "$EDITOR" ]]; then
        "$EDITOR" "$BANNER_FILE"
    else
        nano "$BANNER_FILE"
    fi

    echo "[+] Banner updated."
else
    echo "[*] Keeping default banner."
fi

# -------------------------------
# Dependency handling (hybrid)
# -------------------------------
declare -A DEPS=(
  ["psutil"]="python3-psutil"
  ["requests"]="python3-requests"
  ["colorama"]="python3-colorama"
)

for module in "${!DEPS[@]}"; do
    echo "[*] Checking Python module: $module"

    if ! python3 -c "import $module" &> /dev/null; then
        echo "[!] $module not found, trying pip..."
        if python3 -m pip install --user "$module"; then
            echo "[+] Installed $module via pip"
        else
            echo "[!] pip failed, installing via apt..."
            apt update
            apt install -y "${DEPS[$module]}"
        fi
    else
        echo "[+] $module already installed"
    fi
done

echo
echo "[+] Installation complete"
echo "[+] Run with: signaluplink"

echo
read -rp "Run SignalUplink automatically when opening a terminal? (y/N): " AUTORUN

if [[ "$AUTORUN" =~ ^[Yy]$ ]]; then
    SHELL_NAME=$(basename "$SHELL")

    if [[ "$SHELL_NAME" == "bash" ]]; then
        RC_FILE="$HOME/.bashrc"
    elif [[ "$SHELL_NAME" == "zsh" ]]; then
        RC_FILE="$HOME/.zshrc"
    else
        echo "[!] Unsupported shell: $SHELL_NAME"
        RC_FILE=""
    fi

    if [[ -n "$RC_FILE" ]]; then
        # Marker to avoid duplicates
        MARKER="# SignalUplink autorun"

        if ! grep -q "$MARKER" "$RC_FILE" 2>/dev/null; then
            echo "[*] Enabling SignalUplink autorun in $RC_FILE"

            cat <<EOF >> "$RC_FILE"

$MARKER
if [[ \$- == *i* ]]; then
    command -v signaluplink >/dev/null 2>&1 && signaluplink
fi
EOF

            echo "[+] Autorun enabled"
        else
            echo "[*] Autorun already enabled"
        fi
    fi
else
    echo "[*] Autorun skipped"
fi

