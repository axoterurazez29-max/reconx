#!/usr/bin/env bash

set -e

CYAN="\033[96m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
RESET="\033[0m"

echo -e "${CYAN}"
echo " ____                     __  __"
echo "|  _ \\ ___  ___ ___  _ __ \\ \\/ /"
echo "| |_) / _ \\/ __/ _ \\| '_ \\ \\  /"
echo "|  _ <  __/ (_| (_) | | | |/  \\"
echo "|_| \\_\\___|\\___\\___/|_| |_/_/\\_\\"
echo -e "${RESET}"
echo "        ReconX Installer"
echo "============================================"
echo ""

detect_env() {
    if [ -n "$TERMUX_VERSION" ] || [ -d "/data/data/com.termux" ]; then
        ENV="termux"
        PKG_MGR="pkg install -y"
    elif command -v apt >/dev/null 2>&1; then
        ENV="debian"
        PKG_MGR="sudo apt install -y"
    elif command -v brew >/dev/null 2>&1; then
        ENV="macos"
        PKG_MGR="brew install"
    else
        ENV="unknown"
        PKG_MGR=""
    fi
    echo -e "${CYAN}[*] Environment: ${ENV}${RESET}"
}

install_python_deps() {
    echo -e "${CYAN}[*] Installing Python packages...${RESET}"
    if command -v pip3 >/dev/null 2>&1; then
        pip3 install -r requirements.txt
    elif command -v pip >/dev/null 2>&1; then
        pip install -r requirements.txt
    else
        echo -e "${RED}[!] pip not found. Install Python first.${RESET}"
        exit 1
    fi
    echo -e "${GREEN}[+] Python packages installed.${RESET}"
}

install_system_packages() {
    echo ""
    echo -e "${CYAN}[*] Installing system packages...${RESET}"

    if [ -z "$PKG_MGR" ]; then
        echo -e "${YELLOW}[!] Unknown package manager. Skipping.${RESET}"
        return
    fi

    case "$ENV" in
        termux)
            $PKG_MGR nmap whois dnsutils golang git curl 2>/dev/null || true
            ;;
        debian)
            $PKG_MGR nmap whois dnsutils golang-go git curl 2>/dev/null || true
            ;;
        macos)
            $PKG_MGR nmap whois git curl go 2>/dev/null || true
            ;;
    esac

    echo -e "${GREEN}[+] System packages checked.${RESET}"
}

install_go_tools() {
    echo ""
    echo -e "${CYAN}[*] Installing Go-based recon tools...${RESET}"

    if ! command -v go >/dev/null 2>&1; then
        echo -e "${YELLOW}[!] Go not installed. Install Go, then rerun.${RESET}"
        return
    fi

    export GOPATH="${GOPATH:-$HOME/go}"
    export PATH="$PATH:$GOPATH/bin:$HOME/go/bin"

    install_go_tool() {
        local name="$1"
        local pkg="$2"

        if command -v "$name" >/dev/null 2>&1; then
            echo -e "  ${GREEN}[OK]${RESET}      $name"
        else
            echo -e "  ${CYAN}[INSTALL] $name${RESET}"
            go install -v "$pkg" 2>&1 | tail -1 || echo -e "  ${RED}[FAIL]    $name${RESET}"
        fi
    }

    install_go_tool "subfinder"   "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
    install_go_tool "httpx"       "github.com/projectdiscovery/httpx/cmd/httpx@latest"
    install_go_tool "nuclei"      "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
    install_go_tool "dnsx"        "github.com/projectdiscovery/dnsx/cmd/dnsx@latest"
    install_go_tool "assetfinder" "github.com/tomnomnom/assetfinder@latest"
    install_go_tool "ffuf"        "github.com/ffuf/ffuf/v2@latest"
    install_go_tool "gobuster"    "github.com/OJ/gobuster/v3@latest"

    echo -e "${GREEN}[+] Go tools checked.${RESET}"
}

verify_tools() {
    echo ""
    echo -e "${CYAN}[*] Final verification:${RESET}"
    echo ""

    local tools=(nmap whois dig subfinder httpx nuclei ffuf gobuster assetfinder dnsx)
    local missing=0

    for tool in "${tools[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            printf "  ${GREEN}[OK]${RESET}      %-15s\n" "$tool"
        else
            printf "  ${RED}[MISSING]${RESET} %-15s\n" "$tool"
            missing=$((missing + 1))
        fi
    done

    echo ""
    if [ "$missing" -eq 0 ]; then
        echo -e "${GREEN}[+] All tools ready!${RESET}"
    else
        echo -e "${YELLOW}[!] ${missing} tool(s) missing.${RESET}"
    fi
}

detect_env
install_python_deps
install_system_packages
install_go_tools
verify_tools

echo ""
echo -e "${GREEN}============================================${RESET}"
echo -e "${GREEN}[+] ReconX installation complete!${RESET}"
echo -e "${GREEN}[+] Run: python3 reconx.py --help${RESET}"
echo -e "${GREEN}============================================${RESET}"
