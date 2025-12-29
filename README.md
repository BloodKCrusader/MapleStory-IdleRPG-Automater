# MapleStory Idle Bot

A Python automation bot for MapleStory Idle running on BlueStacks. Automates party quests by reading the screen and simulating inputs through ADB.

This bot does not modify the game. It only reads pixels and sends touch inputs.

## Disclaimer

This project is for **educational purposes only**. It is free to use, modify, and distribute. The authors assume no responsibility for any consequences resulting from the use of this software. Use at your own risk.

## Features

- Auto Party Quest with queue timeout handling
- Quest selection (Sleepywood, Ludibrium)
- Auto recovery from stuck states and connection loss
- Random jump actions during PQ
- GUI and CLI modes

## Requirements

### BlueStacks Setup

1. Resolution: 960 x 540
2. Pixel Density: 240 DPI
3. ADB Enabled: Settings > Advanced > Android Debug Bridge
4. Restart BlueStacks after enabling ADB

### Python Dependencies

```bash
pip install -r requirements.txt
```

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create templates (first time only):
```bash
python tools/template_creator.py --port 5555
```

3. Run the bot:
```bash
# GUI mode
python main.py

# CLI mode
python main.py --cli --port 5555 --quest sleepywood
```

## Project Structure

```
maple_bot/
├── main.py                 # Entry point
├── config.py               # Configuration management
├── core/                   # ADB, screen capture, template matching, input
├── games/                  # Game-specific bot logic
├── gui/                    # GUI launcher
├── tools/                  # Template creator utility
├── templates/              # Template images for matching
└── config/                 # Settings files
```

## Configuration

Copy the example config and edit:
```bash
cp config/settings.yaml.example config/settings.yaml
```

Edit `config/settings.yaml`:

```yaml
adb:
  host: "127.0.0.1"
  port: 5555

bot-option:
  queue-timeout: 30
  quest-choice: sleepywood
  random-jump: true
```

## CLI Options

```
--cli           Run in command-line mode
--port, -p      ADB port (default: 5555)
--quest, -q     Quest type: sleepywood, ludibrium
--debug, -d     Enable debug logging
--create-config Create default configuration file
```

## License

MIT License
