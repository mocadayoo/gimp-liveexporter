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
        CONFIG_HOME="$HOME/Library/Application Support"
        ;;
    Linux)
        CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
        ;;
    *)
        echo "未対応のOSです: $(uname -s)" >&2
        echo "このインストーラーはmacOSとLinuxに対応しています。Windowsではinstall.batを使用してください。" >&2
        exit 1
        ;;
esac

if [ -n "${GIMP3_DIRECTORY:-}" ]; then
    case "$GIMP3_DIRECTORY" in
        /*) GIMP_DIRECTORY="$GIMP3_DIRECTORY" ;;
        *) GIMP_DIRECTORY="$HOME/$GIMP3_DIRECTORY" ;;
    esac
else
    GIMP_VERSION=$(find "$CONFIG_HOME/GIMP" -mindepth 1 -maxdepth 1 -type d -name '3.*' -exec basename {} \; 2>/dev/null \
        | grep -E '^3\.[0-9]+(\.[0-9]+)*$' \
        | sort -t . -k1,1n -k2,2n -k3,3n \
        | tail -n 1)

    if [ -z "$GIMP_VERSION" ]; then
        echo "GIMPの設定フォルダが見つかりません。先にGIMPを一度起動してから、もう一度実行してください。" >&2
        echo "別の場所を使う場合は、GIMP3_DIRECTORYに設定フォルダを指定してください。" >&2
        exit 1
    fi

    GIMP_DIRECTORY="$CONFIG_HOME/GIMP/$GIMP_VERSION"
fi

PLUGIN_DIRECTORY="$GIMP_DIRECTORY/plug-ins/gimp-liveexporter"
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
