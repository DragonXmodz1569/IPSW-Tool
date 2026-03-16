# DragonXmodz1569 IPSW Tool

A simple Python tool for working with Apple IPSW firmware files.

## Current Features
- GUI Support
- Console
- Offline Mode
- Multi IOS Actioning
- Downloading iPhone Updates
- Supports only iPhone At moment
- no root required

## In Progress
- GUI support (PySide6 interface being built)
- Updates Database grabber to work with Stage 1 IPSW file
- Add button to check what stage a file on, delete file extracted directory, refresh database

## Planned Features
- Support all Apple devices (iPhone, iPad, iPod, etc.)
- Support iOS versions from 1 → latest
- Integration with Ollama AI for file analysis
- AI learning / memory features for automation
- Support Multi Platform (spread out to windows and linux next)
- Multiple API for more AI with custom prompts changing ability (so can jailbreak it)
- Add CLI Menu

## Requirements
- macOS (Built on Macbook Pro 2024 M4 with 24GB RAM running Tahoe 26.3.1 as of post)
- Python 3.14+
- Partial Wifi (Mainly for first run to get Database and Download IPSW Files)
- Tools used:
  - `hdiutil`
  - `7z`
  - `IPSW`

## Example Usage
```bash
python main.py