# ReconX

⚡ **Tools made by Kyoraku**

A modular reconnaissance framework for authorized security testing. ReconX wraps industry-standard tools and produces a clean white-background HTML report.

## Features

- Modular architecture — enable only what you need
- Wraps nmap, subfinder, assetfinder, dnsx, httpx, ffuf, gobuster, nuclei, whois, dig
- Clean white HTML report with severity coloring
- JSON output for automation
- Rich terminal UI with live progress
- Runs on Termux, Linux, macOS

## Modules

| Module | Tools | Purpose |
|--------|-------|---------|
| `subdomain` | subfinder, assetfinder, dnsx | Subdomain enumeration |
| `portscan` | nmap | Port and service scanning |
| `webprobe` | httpx | Live web host detection |
| `dirbrute` | ffuf, gobuster | Directory discovery |
| `vulnscan` | nuclei | Vulnerability scanning |
| `osint` | whois, dig | Domain intelligence |

## Installation

```bash
git clone https://github.com/axoterurazez29-max/reconx.git
cd reconx
chmod +x install.sh reconx.py
./install.sh
```

## Usage

```bash
# List modules
python3 reconx.py -t example.com --list-modules

# Run specific modules
python3 reconx.py -t example.com -m subdomain,portscan

# Run everything
python3 reconx.py -t example.com --all

# Custom port range
python3 reconx.py -t example.com -m portscan --ports 1-65535
```

## Output Structure

```
output/example_com_20260912_180405/
├── results.json          # Combined data
├── report.html           # HTML report
└── raw/                  # Raw tool output
    ├── subfinder.txt
    ├── nmap.xml
    └── whois.txt
```

## Legal

For authorized security testing only. Use only against systems you own or have written permission to test.

## Author

**Kyoraku**

---

⚡ Tools made by Kyoraku
