#!/usr/bin/env sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SOURCE_FILE="$SCRIPT_DIR/src/gimp-liveexporter.py"
ASSUME_YES=false

if [ "${1:-}" = "--yes" ] || [ "${1:-}" = "-y" ]; then
    ASSUME_YES=true
elif [ "$#" -ne 0 ]; then
    echo "使い方: $0 [--yes]" >&2
    exit 2
fi

case "$(uname -s)" in
    Darwin)
        PLUGIN_DIRECTORY="${HOME}/Library/Application Support/GIMP/3.0/plug-ins/gimp-liveexporter"
        ;;
    Linux)
        CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
        PLUGIN_DIRECTORY="$CONFIG_HOME/GIMP/3.0/plug-ins/gimp-liveexporter"
        ;;
    *)
        echo "未対応のOSです: $(uname -s)" >&2
        echo "このインストーラーはmacOSとLinuxに対応しています。Windowsではinstall.batを使用してください。" >&2
        exit 1
        ;;
esac

DESTINATION_FILE="$PLUGIN_DIRECTORY/gimp-liveexporter.py"

confirm_install() {
    if [ "$ASSUME_YES" = true ]; then
        return 0
    fi

    printf '%s [y/N] ' "$1"
    read -r answer || answer=""
    case "$answer" in
        y|Y|yes|YES|Yes) return 0 ;;
        *) return 1 ;;
    esac
}

if [ ! -f "$SOURCE_FILE" ]; then
    echo "gimp-liveexporter.pyが見つかりません。リリースZIPを再ダウンロードして展開してください。" >&2
    exit 1
fi

echo "GIMP Live Exporter を次の場所へインストールします: $PLUGIN_DIRECTORY"
if ! confirm_install "インストールを開始しますか？"; then
    echo "インストールを中止しました。"
    exit 0
fi

if [ -e "$DESTINATION_FILE" ]; then
    echo "既存のプラグインファイルが見つかりました。"
    if ! confirm_install "既存ファイルを上書きして更新します。続行しますか？"; then
        echo "更新を中止しました。"
        exit 0
    fi
fi

mkdir -p "$PLUGIN_DIRECTORY"
cp "$SOURCE_FILE" "$DESTINATION_FILE"
chmod u+x "$DESTINATION_FILE"

echo "GIMP Live Exporter をインストールしました。"
echo "GIMPを再起動してから Filters > LiveSync を開いてください。"
