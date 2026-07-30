# GIMP Live Exporter - [日本語](../../../README.md)

A GIMP 3 plug-in that monitors image changes and automatically exports PNG files to Unity projects and other destinations.

## Demo

![GIMP Live Exporter Demo](https://raw.githubusercontent.com/mocadayoo/gimp-liveexporter/refs/heads/master/docs/assets/demo.gif)

## Why use it?

Instantly preview texture changes for VRChat avatars, worlds, and other projects **without manually exporting PNG files**.

## Features

- Monitor multiple image tabs simultaneously, with independent Start / Stop control for each tab.
- Exports from a duplicated image, so the original XCF and its save state are never modified.
- Exports the current preview without requiring effects or filters to be committed.
- Configure the export delay and PNG compression level for each tab independently.

## Requirements

- GIMP 3.0 or later
- Automatic installer currently supports **Windows** and **macOS** only.

## Installation

Download the latest ZIP package from **GitHub Releases** and extract it anywhere.

### Windows: Automatic Installation

Launch GIMP once and close it.

Double-click `install.bat` in the extracted folder. A confirmation prompt will appear. Type `y` or `yes` to continue.

The installer automatically selects the newest `3.*` configuration directory under `%APPDATA%\GIMP`.

To run it from PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\install.ps1
```

The installer always asks for confirmation on first installation and again before overwriting an existing installation.

### macOS / Linux: Automatic Installation

Launch GIMP once and close it.

Open a terminal in the extracted folder and run:

```sh
bash install.sh
```

To skip confirmation prompts:

```sh
bash install.sh --yes
```

If your GIMP configuration directory is located elsewhere, specify it using the `GIMP3_DIRECTORY` environment variable:

```sh
GIMP3_DIRECTORY="/path/to/GIMP/3.2" bash install.sh
```

The installer automatically detects the latest `GIMP/3.*` configuration directory and asks for confirmation before installing or overwriting files.

### Manual Installation

1. Create a folder named `gimp-liveexporter` inside the `plug-ins` directory of your GIMP configuration folder (for example, `%APPDATA%\GIMP\3.2\plug-ins`).
2. Copy `gimp-liveexporter.py` from the `src` directory into that folder.
3. Completely restart GIMP.

### Starting Live Sync

1. Select the image tab you want to synchronize.
2. Choose **Filters → LiveSync → Start Sync...**
3. Select a PNG output location (for example, your Unity project's `Assets` folder).
4. Enter the output file name and export delay, then click **Start**.

If the menu does not appear after restarting GIMP, verify that `gimp-liveexporter.py` is installed in the correct GIMP plug-ins directory.

## Usage

After starting synchronization, the selected image tab is monitored for visual changes.

When no further changes are detected for the configured delay period, the PNG is automatically exported.

Use **Stop Sync...** to stop synchronization for a specific tab while keeping all other active synchronizations running.

## Disclaimer

- This software is provided **"as is"**, without warranty of any kind, including but not limited to warranties of functionality, compatibility, continued availability, or fitness for a particular purpose.
- You are solely responsible for using this software. The author shall not be liable, to the fullest extent permitted by applicable law, for any data loss, Unity project corruption, texture modifications, workflow interruptions, or any other damages resulting from the use of or inability to use this software.
- This tool may overwrite the specified PNG file. Please ensure you select the correct output path.
- Users are responsible for complying with the licenses and terms of use of GIMP, Unity, and any third-party assets.

## License

[MIT License](../../../LICENSE)