#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GIMP 3で変更があったらPNGを自動エクスポートするplugin"""

import gi
gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gimp, GimpUi, GLib, Gio, Gtk

import hashlib
import json
import os
import re
import sys
import time
import traceback
import uuid

"""
globalなデフォルトの値や、config類の初期化
"""
DEBOUNCE_MS = 800
POLL_INTERVAL_MS = 200
HEARTBEAT_INTERVAL_MS = 1000
STALE_THRESHOLD_MS = 5000
PNG_COMPRESSION_LEVEL = 0
THUMBNAIL_SIZE = 512       # 4Kプロジェクトで検証済み  (色による)
SESSION_DIR = os.path.join(
    GLib.get_user_cache_dir() or "/tmp", "gimp-livesync-sessions"
)


def session_file(image_id):
    """タブごとの制御ファイル。"""
    return os.path.join(SESSION_DIR, "image-%s.json" % image_id)


def read_session(image_id):
    try:
        with open(session_file(image_id), "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def write_session(image_id, **changes):
    """対象タブだけを更新"""
    try:
        os.makedirs(SESSION_DIR, exist_ok=True)
        data = read_session(image_id)
        data.update(changes)
        temporary = session_file(image_id) + ".tmp"
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        os.replace(temporary, session_file(image_id))
    except Exception as error:
        print("[LiveSync] Failed to write session:", error, file=sys.stderr)


def stop_session(image_id, expected_run_id=None):
    """指定した監視だけを停止する。"""
    session = read_session(image_id)
    if expected_run_id is not None and session.get("run_id") != expected_run_id:
        return False
    write_session(image_id, running=False, heartbeat=0)
    return True


def is_stale(session):
    return time.time() * 1000.0 - session.get("heartbeat", 0) > STALE_THRESHOLD_MS


def list_active_sessions():
    sessions = []
    try:
        filenames = os.listdir(SESSION_DIR)
    except OSError:
        return sessions
    for filename in filenames:
        if not (filename.startswith("image-") and filename.endswith(".json")):
            continue
        try:
            image_id = int(filename[6:-5])
        except ValueError:
            continue
        session = read_session(image_id)
        if session.get("running") and not is_stale(session):
            session["image_id"] = image_id
            sessions.append(session)
        elif session.get("running"):
            stop_session(image_id, session.get("run_id"))
    return sessions


def export_texture(image, target_folder, filename_base):
    """エクスポートの処理本体"""
    out_path = os.path.join(target_folder, filename_base + ".png")
    duplicate = image.duplicate()
    try:
        visible_layer = Gimp.Layer.new_from_visible(
            image, duplicate, "LiveSync preview"
        )
        for layer in duplicate.get_layers():
            duplicate.remove_layer(layer)
        duplicate.insert_layer(visible_layer, None, 0)

        output_file = Gio.File.new_for_path(out_path)
        exported = False
        try:
            procedure = Gimp.get_pdb().lookup_procedure("file-png-export")
            if procedure is not None:
                config = procedure.create_config()
                config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
                config.set_property("image", duplicate)
                config.set_property("file", output_file)
                try:
                    config.set_property("compression", PNG_COMPRESSION_LEVEL)
                except Exception:
                    pass
                result = procedure.run(config)
                exported = result.index(0) == Gimp.PDBStatusType.SUCCESS
        except Exception as error:
            print("[LiveSync] PNG export procedure failed:", error, file=sys.stderr)

        if not exported:
            exported = Gimp.file_save(
                run_mode=Gimp.RunMode.NONINTERACTIVE,
                image=duplicate, file=output_file, options=None,
            )
        if exported:
            # 元タブの未保存状態は変更しない。
            Gimp.message("[LiveSync] Exported: %s" % os.path.basename(out_path))
            return True
        Gimp.message("[LiveSync] Export failed: %s" % out_path)
        return False
    except Exception as error:
        Gimp.message("[LiveSync] Export error: %s" % error)
        traceback.print_exc(file=sys.stderr)
        return False
    finally:
        try:
            duplicate.delete()
        except Exception:
            pass


def browse_for_folder(parent):
    dialog = Gtk.FileChooserDialog(
        title="Select Unity Assets Folder", parent=parent,
        action=Gtk.FileChooserAction.SELECT_FOLDER,
    )
    dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_OK", Gtk.ResponseType.OK)
    folder = dialog.get_filename() if dialog.run() == Gtk.ResponseType.OK else None
    dialog.destroy()
    return folder


def sanitize_filename(filename):
    """Windowsで使えるPNGのファイル名だけを受け付ける。"""
    name = os.path.splitext(filename.strip())[0]
    invalid = '<>:"/\\|?*'
    # windowsでファイル名に使用できないため
    reserved = {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4",
                "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2",
                "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}
    if (not name or name in {".", ".."} or name.rstrip(". ") != name
            or any(character in invalid or ord(character) < 32 for character in name)
            or name.split(".")[0].upper() in reserved):
        return None
    return name


def show_start_dialog(default_filename, default_folder="", default_debounce=DEBOUNCE_MS):
    dialog = Gtk.Dialog(title="LiveSync - Start Sync")
    dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Start", Gtk.ResponseType.OK)
    content = dialog.get_content_area()
    content.set_spacing(8)
    content.set_border_width(10)
    grid = Gtk.Grid(column_spacing=8, row_spacing=8)
    content.add(grid)

    folder_entry = Gtk.Entry(text=default_folder, hexpand=True)
    name_entry = Gtk.Entry(text=default_filename, hexpand=True)
    debounce_entry = Gtk.Entry(text=str(default_debounce), hexpand=True)
    error_label = Gtk.Label(xalign=0)
    browse = Gtk.Button(label="Browse...")
    browse.connect("clicked", lambda _: folder_entry.set_text(
        browse_for_folder(dialog) or folder_entry.get_text()))
    grid.attach(Gtk.Label(label="Unity Assets Folder:", halign=Gtk.Align.START), 0, 0, 1, 1)
    grid.attach(folder_entry, 1, 0, 1, 1)
    grid.attach(browse, 2, 0, 1, 1)
    grid.attach(Gtk.Label(label="File name (.png):", halign=Gtk.Align.START), 0, 1, 1, 1)
    grid.attach(name_entry, 1, 1, 2, 1)
    grid.attach(Gtk.Label(label="Export delay (ms):", halign=Gtk.Align.START), 0, 2, 1, 1)
    grid.attach(debounce_entry, 1, 2, 2, 1)
    grid.attach(error_label, 0, 3, 3, 1)
    dialog.show_all()

    result = None
    while dialog.run() == Gtk.ResponseType.OK:
        folder = folder_entry.get_text().strip().strip('"')
        filename = sanitize_filename(name_entry.get_text())
        debounce_text = debounce_entry.get_text().strip()
        if not folder or not os.path.isdir(folder):
            error_label.set_text("Choose an existing output folder.")
        elif not os.access(folder, os.W_OK):
            error_label.set_text("The output folder is not writable.")
        elif filename is None:
            error_label.set_text("ファイル名に使えない文字が含まれています。")
        # 数字だけを受け付ける。
        elif not re.fullmatch(r"[0-9]{1,5}", debounce_text):
            error_label.set_text("Export delay must be a whole number in milliseconds.")
        elif not 50 <= int(debounce_text) <= 60000:
            error_label.set_text("Export delay must be between 50 and 60000 ms.")
        else:
            result = (folder, filename, int(debounce_text))
            break
    dialog.destroy()
    return result


def show_stop_dialog(current_image_id):
    """監視を停止、なお複数tab扱えるので選択式で止める"""
    sessions = list_active_sessions()
    if not sessions:
        return None
    dialog = Gtk.Dialog(title="LiveSync - Stop Sync")
    dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Stop selected", Gtk.ResponseType.OK)
    content = dialog.get_content_area()
    content.set_spacing(8)
    content.set_border_width(10)
    content.add(Gtk.Label(label="Select the tab/session to stop:", xalign=0))
    combo = Gtk.ComboBoxText()
    selected_index = 0
    for index, session in enumerate(sessions):
        image_id = session["image_id"]
        label = "%s  (tab ID %s)  ->  %s.png" % (
            session.get("image_name", "Untitled"), image_id,
            session.get("filename_base", "texture"),
        )
        combo.append(str(image_id), label)
        if image_id == current_image_id:
            selected_index = index
    combo.set_active(selected_index)
    content.add(combo)
    dialog.show_all()
    image_id = None
    if dialog.run() == Gtk.ResponseType.OK:
        chosen = combo.get_active_id()
        image_id = int(chosen) if chosen is not None else None
    dialog.destroy()
    return image_id


def show_replace_dialog(image_name):
    """同じタブの監視を置き換えるか確認"""
    dialog = Gtk.Dialog(title="LiveSync - Replace Sync")
    dialog.add_buttons(
        "_Cancel", Gtk.ResponseType.CANCEL,
        "_Replace", Gtk.ResponseType.OK,
    )
    content = dialog.get_content_area()
    content.set_spacing(8)
    content.set_border_width(10)
    content.add(Gtk.Label(
        label="このタブは既に同期中です。\n現在の同期を停止して、新しい設定で開始しますか？\n\n%s" % image_name,
        xalign=0,
    ))
    dialog.show_all()
    replace = dialog.run() == Gtk.ResponseType.OK
    dialog.destroy()
    return replace


def image_token(image):
    """未保存のtabのpreview画像をhash化 <- 変更の検出用"""
    if not image.is_dirty():
        return None
    thumbnail = image.get_thumbnail(
        THUMBNAIL_SIZE, THUMBNAIL_SIZE, Gimp.PixbufTransparency.KEEP_ALPHA
    )
    pixels = thumbnail.get_pixels()
    header = "%s:%s:%s:%s" % (
        image.get_width(), image.get_height(), thumbnail.get_rowstride(),
        thumbnail.get_n_channels(),
    )
    return hashlib.blake2b(
        header.encode("ascii") + bytes(pixels), digest_size=16
    ).digest()


class LiveSyncPlugin(Gimp.PlugIn):
    def do_set_i18n(self, name):
        return False

    def do_query_procedures(self):
        return ["python-fu-livesync-start", "python-fu-livesync-stop"]

    def do_create_procedure(self, name):
        if name == "python-fu-livesync-start":
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.start_sync, None)
            procedure.set_menu_label("Start Sync...")
            procedure.set_documentation("Start per-tab live sync", "Starts sync only for the selected image tab.", name)
        elif name == "python-fu-livesync-stop":
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.stop_sync, None)
            procedure.set_menu_label("Stop Sync...")
            procedure.set_documentation("Stop a selected live sync", "Choose one running tab to stop; all others continue.", name)
        else:
            return None
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE | Gimp.ProcedureSensitivityMask.NO_DRAWABLES)
        procedure.add_menu_path("<Image>/Filters/LiveSync")
        procedure.set_attribution("LiveSync", "LiveSync", "2026")
        return procedure

    def start_sync(self, procedure, run_mode, image, drawables, config, data):
        if run_mode != Gimp.RunMode.INTERACTIVE or image is None:
            return procedure.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, GLib.Error())

        GimpUi.init("gimp-livesync")
        image_id = image.get_id()
        image_name = image.get_name() or "untitled"
        existing = read_session(image_id)
        replace_existing = existing.get("running") and not is_stale(existing)
        if replace_existing and not show_replace_dialog(image_name):
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

        default_name = os.path.splitext(os.path.basename(image_name))[0] or "texture"
        settings = show_start_dialog(
            default_name, existing.get("target_folder", ""),
            existing.get("debounce_ms", DEBOUNCE_MS),
        )
        if settings is None:
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        target_folder, filename_base, debounce_ms = settings
        if replace_existing:
            # 確認後にだけ既存の監視を止める。
            stop_session(image_id, existing.get("run_id"))
        run_id = uuid.uuid4().hex
        write_session(image_id, running=True, image_name=image_name,
                      target_folder=target_folder, filename_base=filename_base,
                      debounce_ms=debounce_ms, run_id=run_id,
                      heartbeat=time.time() * 1000.0)
        Gimp.message("[LiveSync] Started for tab: %s" % image_name)

        state = {"observed_token": None, "pending_token": None,
                 "pending_since": None, "exported_token": None,
                 "last_heartbeat": 0}
        loop = GLib.MainLoop()

        def poll():
            session = read_session(image_id)
            if not session.get("running") or session.get("run_id") != run_id:
                loop.quit()
                return False
            now = GLib.get_monotonic_time() / 1000.0
            if now - state["last_heartbeat"] >= HEARTBEAT_INTERVAL_MS:
                write_session(image_id, heartbeat=time.time() * 1000.0)
                state["last_heartbeat"] = now
            try:
                token = image_token(image)
            except Exception:
                Gimp.message("[LiveSync] The source tab was closed; sync stopped.")
                loop.quit()
                return False
            # 変更が続く間は待機時間をリセットする。
            if token is not None and token != state["observed_token"]:
                state["observed_token"] = token
                state["pending_token"] = token
                state["pending_since"] = now
            if (state["pending_token"] is not None and state["pending_since"] is not None
                    and now - state["pending_since"] >= debounce_ms):
                token_to_export = state["pending_token"]
                if not export_texture(image, target_folder, filename_base):
                    # 失敗時も変更を保持して次回に再試行する。
                    state["pending_since"] = now
                    return True
                state["exported_token"] = token_to_export
                # 出力中の編集も次回の出力対象にする。
                try:
                    token_after_export = image_token(image)
                except Exception:
                    loop.quit()
                    return False
                state["observed_token"] = token_after_export
                if token_after_export != token_to_export:
                    state["pending_token"] = token_after_export
                    state["pending_since"] = now
                else:
                    state["pending_token"] = None
                    state["pending_since"] = None
            return True

        GLib.timeout_add(POLL_INTERVAL_MS, poll)
        try:
            loop.run()
        finally:
            # 新しい同一タブの監視を止めない。
            stop_session(image_id, run_id)
        Gimp.message("[LiveSync] Stopped for tab: %s" % image_name)
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def stop_sync(self, procedure, run_mode, image, drawables, config, data):
        GimpUi.init("gimp-livesync")
        selected_id = show_stop_dialog(image.get_id() if image is not None else None)
        if selected_id is None:
            Gimp.message("[LiveSync] No active sync session was stopped.")
        else:
            stop_session(selected_id)
            Gimp.message("[LiveSync] Stop requested for tab ID %s." % selected_id)
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(LiveSyncPlugin.__gtype__, sys.argv)
