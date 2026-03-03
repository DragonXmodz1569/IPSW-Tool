# DragonXmodz1569 IPSW Tool

A simple Python tool for working with Apple IPSW firmware files.

## Current Features
- Extract IPSW files
- Decrypt firmware images
- Works with iOS 26 IPSWs (tested with 23D127 builds)
- Console
- Offline Mode

## In Progress
- GUI support (PySide6 interface being built)
- Download iOS firmware automatically (stable + beta)
- Better IPSW mounting & APFS extraction tools

## Planned Features
- Support all Apple devices (iPhone, iPad, iPod, etc.)
- Support iOS versions from 1 → latest
- Integration with Ollama AI for file analysis
- AI learning / memory features for automation
- Support Multi Platform
- Multiple API for more AI with custom prompts changing ability (so can jailbreak it)

## Requirements
- macOS (Built on Tahoe 26.3)
- Python 3.14+
- Tools used:
  - `hdiutil`
  - `7z`
  - `IPSW`
  


## Example Usage
```bash
python main.py