# GIMP Live Exporter

GIMP 3で編集した画像を監視し、Unityプロジェクト等へのPNGへ自動出力するプラグインです。
VRChat用アバター・ワールドのテクスチャ調整を、Unityへの手動の操作なしで確認できます。

## 特長

- タブごとに独立してStart / Stopできる
- 複数タブを同時に監視できる
- 出力は複製画像から行い、元XCFの保存状態や編集内容を変更しない
- 出力中の編集も検出し、次回の出力対象にする
- 変更後の待機時間をタブごとに指定できる

## 動作環境

- GIMP 3.0以降
- Unity（おすすめ: PNGの出力先としてUnityプロジェクトの `Assets` 配下を指定）

## インストール

GitHub ReleasesからZIPをダウンロードし、任意の場所へ展開してください。

### Windows: 自動インストール

展開したフォルダ内の `install.bat` をダブルクリックしてください。確認画面が開くので、内容を確認して `y` または `yes` を入力します。

PowerShellから実行したい場合は、展開したフォルダをPowerShellで開いて次を実行します。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\install.ps1
```

初回でも確認を表示し、既に導入済みの場合は上書き前にもう一度確認します。

インストール先は以下です。

```text
%APPDATA%\GIMP\3.0\plug-ins\gimp-liveexporter\gimp-liveexporter.py
```

### macOS / Linux: 自動インストール

展開したフォルダをターミナルで開き、次を実行してください。初回と既存ファイルの上書き前に確認を表示します。

```sh
./install.sh
```

`./install.sh` を実行できない環境では、次のように実行できます。

```sh
sh install.sh
```

確認なしで実行する場合は `--yes` を付けます。

```sh
./install.sh --yes
```

実行権限がないと表示された場合は、先に `chmod +x install.sh` を実行してください。インストール先は次のとおりです。

- macOS: `~/Library/Application Support/GIMP/3.0/plug-ins/gimp-liveexporter/gimp-liveexporter.py`
- Linux: `${XDG_CONFIG_HOME:-~/.config}/GIMP/3.0/plug-ins/gimp-liveexporter/gimp-liveexporter.py`

### 手動インストール

1. `%APPDATA%\GIMP\3.0\plug-ins\gimp-liveexporter\` フォルダを作成します。
2. `src\gimp-liveexporter.py` をそのフォルダへコピーします。
3. GIMPを完全に終了してから再起動します。

### GIMPで開始する

1. 同期したい画像タブを選びます。
2. `Filters > LiveSync > Start Sync...` を選びます。
3. Unityプロジェクトの `Assets` 配下など、PNGの出力先を指定します。
4. PNG名と出力待機時間を入力してStartします。

GIMPの再起動後にメニューが見つからない場合は、GIMPのプラグインフォルダ設定と `src\gimp-liveexporter.py` の配置先を確認してください。

## 使い方

Start Sync後、対象タブの見た目の変化を監視します。最後の編集から指定時間だけ変化がなければPNGを出力します。

`Stop Sync...` では、稼働中の一覧から停止するタブを1つ選べます。他のタブの同期は継続します。

## 免責事項

- 本ツールは無保証で提供します。動作、互換性、継続利用、特定の目的への適合を保証しません。
- 利用者自身の責任で使用してください。使用または使用不能により生じたデータ消失、Unityプロジェクトの破損、テクスチャ設定の変更、作業中断その他の損害について、作者は適用法令で許される最大限の範囲で責任を負いません。
- 本ツールは指定したPNGを上書きする場合がございます。ファイル指定には気を付けてください。
- Unity、GIMPおよび各アセットの利用規約・ライセンスは、利用者自身で確認してください。

## License

[MIT License](LICENSE)
