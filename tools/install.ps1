$sourceFile = Join-Path $PSScriptRoot "..\src\gimp-liveexporter.py"
$pluginDirectory = Join-Path $env:APPDATA "GIMP\3.0\plug-ins\gimp-liveexporter"
$destinationFile = Join-Path $pluginDirectory "gimp-liveexporter.py"

function Confirm-Install([string]$Prompt) {
    $answer = Read-Host "$Prompt [y/N]"
    return $answer -match '^(?i:y|yes)$'
}

if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
    throw "gimp-liveexporter.pyが見つかりません。リリースZIPを再ダウンロードして展開してください。"
}

Write-Host "GIMP Live Exporter を次の場所へインストールします: $pluginDirectory"
if (-not (Confirm-Install "インストールを開始しますか？")) {
    Write-Host "インストールを中止しました。"
    exit 0
}

if (Test-Path -LiteralPath $destinationFile) {
    Write-Host "既存のプラグインファイルが見つかりました。"
    if (-not (Confirm-Install "既存ファイルを上書きして更新します。続行しますか？")) {
        Write-Host "更新を中止しました。"
        exit 0
    }
}

New-Item -ItemType Directory -Path $pluginDirectory -Force | Out-Null
Copy-Item -LiteralPath $sourceFile -Destination $destinationFile -Force
Unblock-File -LiteralPath $destinationFile -ErrorAction SilentlyContinue

Write-Host "GIMP Live Exporter をインストールしました。"
Write-Host "GIMPを再起動してから Filters > LiveSync を開いてください。"
