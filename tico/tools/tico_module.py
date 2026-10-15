#!/usr/bin/env python3
"""Settings definition and translations for the tico module of bluemsx.

Run after merging upstream. It builds tools/dump_core_options.c against the
core's own libretro_core_options.h, so tico/module/settings.json lists exactly
the options the libnx core reads (bluemsx_* keys, values and defaults), laid
out in tabs, followed by the overlay's own display and controls options.
Labels are translation keys; the strings go into tico/lang/*.json, taken from
the core's own translations, and from the LABELS and CHOICES tables below for
what the core does not translate. Choice labels stay English in settings.json;
the overlay translates them through settings_bluemsx_value_* keys.

    python3 tico/tools/tico_module.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TICO = ROOT / "tico"
SETTINGS = TICO / "module/settings.json"
LANG_DIR = TICO / "lang"
LANGUAGES = ("en", "de", "es", "fr", "ja", "pt", "ru", "zh")
# tico-nx's own strings label the options it already knew; optional
TICO_NX = Path(os.environ.get("TICO_NX_DIR", ROOT.parents[1] / "tico-nx"))

# Core option -> label key. Options are named after their key without bluemsx_.
LABEL_KEYS: dict[str, str] = {}

# Core options the frontend has no use for: both answer to a physical
# keyboard (F12, the number row), which tico does not pass on.
EXCLUDED = {"use_keyboard_for_coleco", "hard_reset_f12"}

# (tab, [(section, [option keys])]). Every core option the dump lists must be
# placed or excluded; the overlay's own tabs are added around these.
LAYOUT = [
    ("settings_bluemsx_tab_system", [
        ("settings_bluemsx_section_machine", ["bluemsx_msxtype", "bluemsx_vdp_synctype",
                                              "bluemsx_rtc_source"]),
        ("settings_bluemsx_section_media", ["bluemsx_cartmapper", "bluemsx_additional_cart",
                                            "bluemsx_auto_rewind_cas"]),
        ("settings_bluemsx_section_colecovision", ["patch_coleco_rom"]),
    ]),
    ("settings_bluemsx_tab_video", [
        ("settings_bluemsx_section_display", ["bluemsx_overscan", "bluemsx_nospritelimits"]),
    ]),
    ("settings_bluemsx_tab_audio", [
        ("settings_bluemsx_section_sound", ["bluemsx_ym2413_enable", "bluemsx_sound_io_enable"]),
    ]),
]

# Listed only while another option has a value, like the core's own menus.
DEPENDS_ON: dict[str, tuple[str, str]] = {}

# English names for values the core leaves in capitals or lower case.
EN_CHOICES = {"ON": "On", "OFF": "Off", "scc": "SCC", "sccexpanded": "SCC (expanded)",
              "sccmirrored": "SCC (mirrored)", "sccplus": "SCC+", "snatcher": "Snatcher",
              "sdsnatcher": "SD Snatcher"}

# Switch buttons a RetroPad button (or the fast-forward hotkey) can sit on.
SWITCH_BUTTONS = [("A", "A"), ("B", "B"), ("X", "X"), ("Y", "Y"), ("L", "L"), ("R", "R"),
                  ("ZL", "ZL"), ("ZR", "ZR"), ("Plus", "Plus"), ("Minus", "Minus"),
                  ("StickL", "Left stick"), ("StickR", "Right stick"), ("Up", "Up"),
                  ("Down", "Down"), ("Left", "Left"), ("Right", "Right"), ("None", "Disabled")]

POSITIONS = [("hidden", "Hidden"), ("top_left", "Top left"), ("top_right", "Top right"),
             ("bottom_left", "Bottom left"), ("bottom_right", "Bottom right")]

# The overlay's own options: how the game is scaled, fast forward and the HUD.
# Shaders are picked in game (Settings > Shaders): tico cannot see the presets
# on the SD card.
OVERLAY_TAB = ("settings_bluemsx_tab_display", [
    ("settings_bluemsx_section_screen", [
        {"key": "display_mode", "label": "settings_bluemsx_display_mode", "type": "enum",
         "default": "Display", "choices": [("Integer", "Integer"), ("Display", "Display")]},
        {"key": "display_size", "label": "settings_bluemsx_display_size", "type": "enum",
         "default": "4:3", "choices": [("Stretch", "Stretch"), ("4:3", "4:3"), ("16:9", "16:9"),
                                       ("Original", "Original"), ("1x", "1x"), ("2x", "2x"),
                                       ("Auto", "Auto")]},
    ]),
    ("settings_bluemsx_section_fast_forward", [
        {"key": "fast_forward_speed", "label": "settings_bluemsx_fast_forward_speed", "type": "enum",
         "default": "200", "choices": [("150", "150%"), ("200", "200%"), ("300", "300%"),
                                        ("400", "400%"), ("unlimited", "Unlimited")]},
        {"key": "fast_forward_mode", "label": "settings_bluemsx_fast_forward_mode", "type": "enum",
         "default": "hold", "choices": [("hold", "Hold"), ("toggle", "Toggle")]},
        {"key": "fast_forward_hotkey", "label": "settings_bluemsx_fast_forward_hotkey",
         "type": "enum", "default": "ZR", "choices": SWITCH_BUTTONS},
    ]),
    ("settings_bluemsx_section_hud", [
        {"key": "fps_counter_position", "label": "settings_bluemsx_fps_counter", "type": "enum",
         "default": "hidden", "choices": POSITIONS},
        {"key": "rendered_ir_position", "label": "settings_bluemsx_rendered_resolution",
         "type": "enum", "default": "hidden", "choices": POSITIONS},
    ]),
])

CONTROLLERS = [("joystick", "Joystick"), ("keyboard", "Keyboard keys")]

# The overlay's controls (TicoMain.cpp): each controller port as an MSX
# joystick or as keys, and each RetroPad button the core reads on a Switch
# button, by default its namesake (the stick clicks for L3/R3). ZR is the
# fast-forward button, so R2 starts on none. The labels say what a button is
# on an MSX joystick and on a ColecoVision controller.
CONTROLS_TAB = ("settings_bluemsx_tab_controls", [
    ("settings_bluemsx_section_controllers", [
        {"key": "controller_1", "label": "settings_bluemsx_controller_1", "type": "enum",
         "default": "joystick", "choices": CONTROLLERS},
        {"key": "controller_2", "label": "settings_bluemsx_controller_2", "type": "enum",
         "default": "joystick", "choices": CONTROLLERS},
    ]),
    ("settings_bluemsx_section_button_mapping", [
        {"key": key, "label": "settings_bluemsx_" + key, "type": "enum", "default": default,
         "choices": SWITCH_BUTTONS}
        for key, default in [
            ("map_up", "Up"), ("map_down", "Down"), ("map_left", "Left"), ("map_right", "Right"),
            ("map_a", "A"), ("map_b", "B"), ("map_x", "X"), ("map_y", "Y"),
            ("map_l", "L"), ("map_r", "R"), ("map_zl", "ZL"), ("map_zr", "None"),
            ("map_l3", "StickL"), ("map_r3", "StickR"),
            ("map_start", "Plus"), ("map_select", "Minus"),
        ]
    ] + [
        {"key": "analog_dpad", "label": "settings_bluemsx_analog_dpad", "type": "bool",
         "default": "enabled"},
    ]),
])

# Labels the core does not define. key -> (en, de, es, fr, ja, pt, ru, zh)
LABELS = {
    "settings_bluemsx_tab_system": ("System", "System", "Sistema", "Système", "システム", "Sistema",
                                    "Система", "系统"),
    "settings_bluemsx_section_machine": ("Machine", "Gerät", "Máquina", "Machine", "本体",
                                         "Máquina", "Машина", "机型"),
    "settings_bluemsx_section_media": ("Cartridges and tapes", "Module und Kassetten",
                                       "Cartuchos y cintas", "Cartouches et cassettes",
                                       "カートリッジとテープ", "Cartuchos e fitas",
                                       "Картриджи и кассеты", "卡带与磁带"),
    "settings_bluemsx_section_colecovision": ("ColecoVision",) * 8,
    "settings_bluemsx_tab_video": ("Video", "Video", "Vídeo", "Vidéo", "ビデオ", "Vídeo", "Видео",
                                   "视频"),
    "settings_bluemsx_section_display": ("Display", "Anzeige", "Pantalla", "Affichage", "表示",
                                         "Exibição", "Отображение", "显示"),
    "settings_bluemsx_tab_audio": ("Audio", "Audio", "Audio", "Audio", "オーディオ", "Áudio", "Звук",
                                   "音频"),
    "settings_bluemsx_section_sound": ("Sound", "Ton", "Sonido", "Son", "サウンド", "Som", "Звук",
                                       "声音"),
    "settings_bluemsx_tab_display": ("Display", "Anzeige", "Pantalla", "Affichage", "表示", "Tela",
                                     "Экран", "显示"),
    "settings_bluemsx_section_screen": ("Screen", "Bild", "Imagen", "Image", "画面", "Imagem",
                                        "Изображение", "画面"),
    "settings_bluemsx_section_hud": ("On-screen info", "Bildschirmanzeige", "Información en pantalla",
                                     "Affichage à l'écran", "画面表示", "Informações na tela",
                                     "Экранная информация", "屏幕信息"),
    "settings_bluemsx_display_mode": ("Display Mode", "Anzeigemodus", "Modo de pantalla",
                                      "Mode d'affichage", "表示モード", "Modo de exibição",
                                      "Режим отображения", "显示模式"),
    "settings_bluemsx_display_size": ("Size", "Größe", "Tamaño", "Taille", "サイズ", "Tamanho",
                                      "Размер", "尺寸"),
    "settings_bluemsx_fps_counter": ("FPS counter", "FPS-Zähler", "Contador de FPS",
                                     "Compteur de FPS", "FPSカウンター", "Contador de FPS",
                                     "Счётчик FPS", "帧率计数器"),
    "settings_bluemsx_rendered_resolution": ("Rendered resolution", "Gerenderte Auflösung",
                                             "Resolución renderizada", "Résolution de rendu",
                                             "描画解像度", "Resolução renderizada",
                                             "Разрешение рендеринга", "渲染分辨率"),
    "settings_bluemsx_section_fast_forward": ("Fast Forward", "Vorspulen", "Avance rápido",
                                              "Avance rapide", "早送り", "Avanço rápido",
                                              "Перемотка", "快进"),
    "settings_bluemsx_fast_forward_speed": ("Fast forward speed", "Vorspul-Geschwindigkeit",
                                            "Velocidad de avance rápido", "Vitesse d'avance rapide",
                                            "早送りの速度", "Velocidade do avanço rápido",
                                            "Скорость перемотки", "快进速度"),
    "settings_bluemsx_fast_forward_mode": ("Fast forward mode", "Vorspul-Modus",
                                           "Modo de avance rápido", "Mode d'avance rapide",
                                           "早送りモード", "Modo do avanço rápido",
                                           "Режим перемотки", "快进模式"),
    "settings_bluemsx_fast_forward_hotkey": ("Fast forward button", "Vorspul-Taste",
                                             "Botón de avance rápido", "Bouton d'avance rapide",
                                             "早送りボタン", "Botão do avanço rápido",
                                             "Кнопка перемотки", "快进按键"),
    "settings_bluemsx_tab_controls": ("Controls", "Steuerung", "Controles", "Commandes", "操作",
                                      "Controles", "Управление", "控制"),
    "settings_bluemsx_section_controllers": ("Controllers", "Controller", "Mandos", "Manettes",
                                             "コントローラー", "Controles", "Контроллеры",
                                             "控制器"),
    "settings_bluemsx_controller_1": ("Player 1", "Spieler 1", "Jugador 1", "Joueur 1",
                                      "プレイヤー1", "Jogador 1", "Игрок 1", "玩家1"),
    "settings_bluemsx_controller_2": ("Player 2", "Spieler 2", "Jugador 2", "Joueur 2",
                                      "プレイヤー2", "Jogador 2", "Игрок 2", "玩家2"),
    "settings_bluemsx_section_button_mapping": ("Button mapping (MSX / ColecoVision)",
                                                "Tastenbelegung (MSX / ColecoVision)",
                                                "Asignación de botones (MSX / ColecoVision)",
                                                "Attribution des boutons (MSX / ColecoVision)",
                                                "ボタン割り当て（MSX / ColecoVision）",
                                                "Mapeamento de botões (MSX / ColecoVision)",
                                                "Назначение кнопок (MSX / ColecoVision)",
                                                "按键映射（MSX / ColecoVision）"),
    "settings_bluemsx_map_up": ("D-Pad Up", "Steuerkreuz oben", "Cruceta arriba", "Croix haut",
                                "十字キー上", "Direcional para cima", "Крестовина вверх",
                                "方向键上"),
    "settings_bluemsx_map_down": ("D-Pad Down", "Steuerkreuz unten", "Cruceta abajo", "Croix bas",
                                  "十字キー下", "Direcional para baixo", "Крестовина вниз",
                                  "方向键下"),
    "settings_bluemsx_map_left": ("D-Pad Left", "Steuerkreuz links", "Cruceta izquierda",
                                  "Croix gauche", "十字キー左", "Direcional para a esquerda",
                                  "Крестовина влево", "方向键左"),
    "settings_bluemsx_map_right": ("D-Pad Right", "Steuerkreuz rechts", "Cruceta derecha",
                                   "Croix droite", "十字キー右", "Direcional para a direita",
                                   "Крестовина вправо", "方向键右"),
    "settings_bluemsx_msxtype": ("Machine Type", "Gerätetyp", "Tipo de máquina", "Type de machine",
                                 "本体の種類", "Tipo de máquina", "Тип машины", "机型"),
    "settings_bluemsx_vdp_synctype": ("VDP sync", "VDP-Synchronisation", "Sincronización del VDP",
                                      "Synchronisation du VDP", "VDP同期", "Sincronização do VDP",
                                      "Синхронизация VDP", "VDP 同步"),
    "settings_bluemsx_rtc_source": ("Real-time clock", "Echtzeituhr", "Reloj en tiempo real",
                                    "Horloge temps réel", "リアルタイムクロック", "Relógio em tempo real",
                                    "Часы реального времени", "实时时钟"),
    "settings_bluemsx_cartmapper": ("Cartridge mapper", "Modul-Mapper", "Mapper del cartucho",
                                    "Mapper de la cartouche", "カートリッジのマッパー",
                                    "Mapper do cartucho", "Маппер картриджа", "卡带映射器"),
    "settings_bluemsx_additional_cart": ("Extra sound cartridge", "Zusätzliches Soundmodul",
                                         "Cartucho de sonido adicional",
                                         "Cartouche son supplémentaire", "追加サウンドカートリッジ",
                                         "Cartucho de som adicional", "Дополнительный звуковой картридж",
                                         "附加音效卡带"),
    "settings_bluemsx_auto_rewind_cas": ("Rewind tapes automatically", "Kassetten automatisch zurückspulen",
                                         "Rebobinar cintas automáticamente",
                                         "Rembobiner les cassettes automatiquement",
                                         "テープを自動で巻き戻す", "Rebobinar fitas automaticamente",
                                         "Автоматически перематывать кассеты", "自动倒带"),
    "settings_bluemsx_patch_coleco_rom": ("Fast BIOS boot", "Schneller BIOS-Start",
                                          "Arranque rápido de la BIOS", "Démarrage rapide du BIOS",
                                          "BIOSを高速起動", "Inicialização rápida da BIOS",
                                          "Быстрый запуск BIOS", "BIOS 快速启动"),
    "settings_bluemsx_overscan": ("Crop overscan", "Overscan abschneiden", "Recortar sobrebarrido",
                                  "Rogner le surbalayage", "オーバースキャンを切り取る",
                                  "Cortar overscan", "Обрезать оверскан", "裁剪过扫描"),
    "settings_bluemsx_nospritelimits": ("No sprite limit", "Kein Sprite-Limit",
                                        "Sin límite de sprites", "Pas de limite de sprites",
                                        "スプライト制限なし", "Sem limite de sprites",
                                        "Без лимита спрайтов", "无精灵数量限制"),
    "settings_bluemsx_ym2413_enable": ("MSX-MUSIC (YM2413)", "MSX-MUSIC (YM2413)",
                                       "MSX-MUSIC (YM2413)", "MSX-MUSIC (YM2413)",
                                       "MSX-MUSIC（YM2413）", "MSX-MUSIC (YM2413)",
                                       "MSX-MUSIC (YM2413)", "MSX-MUSIC（YM2413）"),
    "settings_bluemsx_sound_io_enable": ("Disk drive sounds", "Laufwerksgeräusche",
                                         "Sonidos de la disquetera", "Bruits du lecteur de disquettes",
                                         "ディスクドライブの音", "Sons da unidade de disquete",
                                         "Звуки дисковода", "磁盘驱动器声音"),
    "settings_bluemsx_analog_dpad": ("Left stick as D-Pad", "Linker Stick als Steuerkreuz",
                                     "Stick izquierdo como cruceta",
                                     "Stick gauche comme croix directionnelle",
                                     "左スティックを十字キーとして使う",
                                     "Analógico esquerdo como direcional",
                                     "Левый стик как крестовина", "左摇杆作为方向键"),
}

# The mapping's labels: the RetroPad button, then what it is on an MSX
# joystick and on a ColecoVision controller (libretro.c's btn_map and its
# Coleco keypad). Words per language: (button, key, left fire, right fire,
# keyboard).
_WORDS = [
    ("Button", "Key", "Left fire", "Right fire", "Keyboard"),
    ("Taste", "Taste", "Linker Feuerknopf", "Rechter Feuerknopf", "Tastatur"),
    ("Botón", "Tecla", "Disparo izquierdo", "Disparo derecho", "Teclado"),
    ("Bouton", "Touche", "Tir gauche", "Tir droit", "Clavier"),
    ("ボタン", "キー", "左トリガー", "右トリガー", "キーボード"),
    ("Botão", "Tecla", "Disparo esquerdo", "Disparo direito", "Teclado"),
    ("Кнопка", "Клавиша", "Левая кнопка огня", "Правая кнопка огня", "Клавиатура"),
    ("按钮", "键", "左开火键", "右开火键", "键盘"),
]
for _key, _pad, _msx, _coleco in [
    ("map_a", "A", ("button", 1), ("left",)), ("map_b", "B", ("button", 2), ("right",)),
    ("map_y", "Y", ("button", 3), ("key", "2")), ("map_x", "X", ("button", 4), ("key", "1")),
    ("map_l", "L", None, ("key", "4")), ("map_r", "R", None, ("key", "3")),
    ("map_zl", "ZL", None, ("key", "6")), ("map_zr", "ZR", None, ("key", "5")),
    ("map_l3", "L3", None, ("key", "8")), ("map_r3", "R3", None, ("key", "7")),
    ("map_start", "Start", ("button", 5), ("key", "#")),
    ("map_select", "Select", ("keyboard",), ("key", "*")),
]:
    def _say(part, words):
        if part is None:
            return "—"
        kind = part[0]
        if kind == "button":
            return f"{words[0]} {part[1]}"
        if kind == "key":
            return f"{words[1]} {part[1]}"
        return {"left": words[2], "right": words[3], "keyboard": words[4]}[kind]
    LABELS["settings_bluemsx_" + _key] = tuple(
        f"{_pad}: {_say(_msx, words)} / {_say(_coleco, words)}" for words in _WORDS)

# Choice labels the core does not translate. English -> (de, es, fr, ja, pt, ru, zh)
CHOICES = {
    "Joystick": ("Joystick", "Joystick", "Joystick", "ジョイスティック", "Joystick", "Джойстик",
                 "摇杆"),
    "Keyboard keys": ("Tastaturtasten", "Teclas del teclado", "Touches du clavier", "キーボードのキー",
                      "Teclas do teclado", "Клавиши клавиатуры", "键盘按键"),
    "On": ("An", "Activado", "Activé", "オン", "Ligado", "Вкл.", "开"),
    "Host Clock": ("Uhr der Konsole", "Reloj de la consola", "Horloge de la console", "本体の時計",
                   "Relógio do console", "Часы консоли", "主机时钟"),
    "Fixed Epoch (deterministic)": ("Fester Zeitpunkt (deterministisch)",
                                    "Época fija (determinista)", "Date fixe (déterministe)",
                                    "固定日時（決定的）", "Época fixa (determinística)",
                                    "Фиксированная дата (детерминированно)", "固定时间（确定性）"),
    "Off": ("Aus", "Desactivado", "Désactivé", "オフ", "Desligado", "Выкл.", "关"),
    "Disabled": ("Deaktiviert", "Desactivado", "Désactivé", "無効", "Desativado", "Выключено",
                 "禁用"),
    "Enabled": ("Aktiviert", "Activado", "Activé", "有効", "Ativado", "Включено", "启用"),
    "Integer": ("Ganzzahlig", "Entero", "Entier", "整数倍", "Inteiro", "Целочисленный", "整数"),
    "Display": ("Anzeige", "Pantalla", "Écran", "画面", "Tela", "Экран", "屏幕"),
    "Stretch": ("Strecken", "Estirar", "Étirer", "引き伸ばし", "Esticar", "Растянуть", "拉伸"),
    "Original": ("Original", "Original", "Original", "オリジナル", "Original", "Оригинал", "原始"),
    "Auto": ("Auto", "Auto", "Auto", "自動", "Auto", "Авто", "自动"),
    "Unlimited": ("Unbegrenzt", "Ilimitado", "Illimité", "無制限", "Ilimitado", "Без ограничений",
                  "无限制"),
    "Hold": ("Halten", "Mantener", "Maintenir", "長押し", "Segurar", "Удерживать", "按住"),
    "Toggle": ("Umschalten", "Alternar", "Basculer", "切り替え", "Alternar", "Переключать", "切换"),
    "Right stick": ("Rechter Stick", "Stick derecho", "Stick droit", "右スティック", "Analógico direito",
                    "Правый стик", "右摇杆"),
    "Left stick": ("Linker Stick", "Stick izquierdo", "Stick gauche", "左スティック", "Analógico esquerdo",
                   "Левый стик", "左摇杆"),
    "Plus": ("Plus", "Más", "Plus", "プラス", "Mais", "Плюс", "加号"),
    "Minus": ("Minus", "Menos", "Moins", "マイナス", "Menos", "Минус", "减号"),
    "Up": ("Oben", "Arriba", "Haut", "上", "Cima", "Вверх", "上"),
    "Down": ("Unten", "Abajo", "Bas", "下", "Baixo", "Вниз", "下"),
    "Left": ("Links", "Izquierda", "Gauche", "左", "Esquerda", "Влево", "左"),
    "Right": ("Rechts", "Derecha", "Droite", "右", "Direita", "Вправо", "右"),
    "Hidden": ("Ausgeblendet", "Oculto", "Masqué", "非表示", "Oculto", "Скрыто", "隐藏"),
    "Top left": ("Oben links", "Arriba a la izquierda", "En haut à gauche", "左上",
                 "Superior esquerdo", "Сверху слева", "左上"),
    "Top right": ("Oben rechts", "Arriba a la derecha", "En haut à droite", "右上",
                  "Superior direito", "Сверху справа", "右上"),
    "Bottom left": ("Unten links", "Abajo a la izquierda", "En bas à gauche", "左下",
                    "Inferior esquerdo", "Снизу слева", "左下"),
    "Bottom right": ("Unten rechts", "Abajo a la derecha", "En bas à droite", "右下",
                     "Inferior direito", "Снизу справа", "右下"),
}

RESTART_SUFFIX = re.compile(r"\s*\((Close Content|Restart Required|Restart|Reload Core|[^)]*[Nn]eustart[^)]*|[^)]*[Rr]einici[^)]*|"
                            r"[^)]*[Rr]edémarr[^)]*|[^)]*再起動[^)]*|[^)]*перезапуск[^)]*|"
                            r"[^)]*重启[^)]*|[^)]*[Rr]einicializa[^)]*)\)")


def value_key(label: str) -> str:
    """tico_config.cpp's ValueKey: settings_bluemsx_value_ + label as a slug."""
    return "settings_bluemsx_value_" + "_".join(re.findall(r"[a-z0-9]+", label.lower()))


def clean_label(text: str) -> str:
    return RESTART_SUFFIX.sub("", text).lstrip("> ").strip()


def english_choice(value: str, label: str) -> str:
    # the core leaves on/off style values unlabelled
    if label == value and value in ("disabled", "enabled"):
        return label.capitalize()
    return EN_CHOICES.get(label, label)


def dump_options() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(tmp) / "dump_core_options"
        subprocess.run(["cc", "-std=gnu11", "-w",
                        "-I", str(ROOT),
                        "-I", str(ROOT / "libretro-common/include"),
                        "-o", str(exe), str(Path(__file__).with_name("dump_core_options.c"))],
                       check=True)
        return json.loads(subprocess.run([str(exe)], check=True, capture_output=True,
                                         text=True).stdout)


def label_key(key: str) -> str:
    return LABEL_KEYS.get(key, "settings_bluemsx_" + key.removeprefix("bluemsx_"))


def build_settings(dump: dict) -> dict:
    core = {o["key"]: o for o in dump["en"]}
    placed = {key for _, sections in LAYOUT for _, keys in sections for key in keys}
    missing = sorted(set(core) - placed - EXCLUDED)
    if missing:
        raise SystemExit(f"core options not placed in LAYOUT: {missing}")

    tabs = []
    for tab, sections in LAYOUT:
        out_sections = []
        for title, keys in sections:
            options = []
            for key in keys:
                source = core[key]
                values = [v for v, _ in source["values"]]
                option = {"key": key, "label": label_key(key)}
                # a default the core does not list (its "None" for the sound
                # cartridge) is its first choice, as the core treats it
                default = source["default"] if source["default"] in values else values[0]
                if sorted(values) == ["disabled", "enabled"]:
                    option.update(type="bool", default=default)
                else:
                    option.update(type="enum", default=default, choices=[
                        {"label": english_choice(v, l), "value": v} for v, l in source["values"]])
                if RESTART_SUFFIX.search(source["desc"]):
                    option["restart"] = True
                if key in DEPENDS_ON:
                    on, value = DEPENDS_ON[key]
                    option["depends_on"] = {"key": on, "value": value}
                options.append(option)
            out_sections.append({"title": title, "options": options})
        tabs.append({"name": tab, "sections": out_sections})

    def overlay_tab(definition):
        tab, sections = definition
        return {"name": tab, "sections": [
            {"title": title, "options": [
                {**o, "choices": [{"label": l, "value": v} for v, l in o["choices"]]}
                if "choices" in o else dict(o)
                for o in options]}
            for title, options in sections]}

    tabs.insert(1, overlay_tab(OVERLAY_TAB))
    tabs.append(overlay_tab(CONTROLS_TAB))

    return {
        "core_id": "bluemsx",
        "display_name": "blueMSX",
        "config_file": "bluemsx.jsonc",
        "slugs": ["msx", "msx2", "colecovision", "spectravideo", "sc-3000"],
        "bool_true_value": "enabled",
        "bool_false_value": "disabled",
        "tabs": tabs,
    }


def tico_owned(key: str) -> bool:
    """Labels tico itself defines, whose wording tico keeps."""
    return key in LABEL_KEYS.values() or key.startswith(("settings_bluemsx_tab_",
                                                          "settings_bluemsx_section_"))


def build_strings(dump: dict, settings: dict,
                  existing: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    strings: dict[str, dict[str, str]] = {lang: {} for lang in LANGUAGES}
    english = {o["key"]: o for o in dump["en"]}
    for lang in LANGUAGES:
        out = strings[lang]
        index = LANGUAGES.index(lang)
        for option in dump[lang]:
            if option["key"] in EXCLUDED or option["key"] not in english:
                continue
            key, en = option["key"], english[option["key"]]
            # a language the core leaves empty falls back to English
            if clean_label(option["desc"]):
                out[label_key(key)] = clean_label(option["desc"])
            # by value: a translation may list the choices differently
            en_labels = dict(en["values"])
            for value, label in option["values"]:
                if label is None or value not in en_labels:
                    continue
                en_text = english_choice(value, en_labels[value])
                if label != en_labels[value]:
                    out[value_key(en_text)] = label
        for key, texts in LABELS.items():
            out[key] = texts[index]
        if lang != "en":
            for choice, translations in CHOICES.items():
                out[value_key(choice)] = translations[index - 1]
        if lang == "en":
            for key in list(out):
                if key.startswith("settings_bluemsx_value_"):
                    del out[key]
    # tico's own labels keep tico's wording: from tico-nx when it is checked
    # out, otherwise as the language files already have them
    for lang in LANGUAGES:
        path = TICO_NX / "assets/lang" / f"{lang}.json"
        source = json.loads(path.read_text()) if path.exists() else existing[lang]
        for key, value in source.items():
            if tico_owned(key):
                strings[lang][key] = value
    used = set()

    def walk(node):
        if isinstance(node, dict):
            for field in ("label", "name", "title"):
                if isinstance(node.get(field), str) and node[field].startswith("settings_"):
                    used.add(node[field])
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(settings)
    unlabelled = sorted(used - set(strings["en"]))
    if unlabelled:
        raise SystemExit(f"labels without English text: {unlabelled}")
    return strings


def main() -> None:
    dump = dump_options()
    settings = build_settings(dump)
    SETTINGS.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")
    current_files = {lang: json.loads((LANG_DIR / f"{lang}.json").read_text())
                     if (LANG_DIR / f"{lang}.json").exists() else {} for lang in LANGUAGES}
    for lang, strings in build_strings(dump, settings, current_files).items():
        path = LANG_DIR / f"{lang}.json"
        current = {k: v for k, v in current_files[lang].items()
                   if not k.startswith("settings_bluemsx_")}
        current.update(dict(sorted(strings.items())))
        path.write_text(json.dumps(current, indent=4, ensure_ascii=False) + "\n")
    print(f"wrote {SETTINGS.relative_to(ROOT)} and {len(LANGUAGES)} language files")


if __name__ == "__main__":
    main()
