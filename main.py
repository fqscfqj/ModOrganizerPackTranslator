import customtkinter as ctk
import openai
import os
import shutil
import threading
import queue
import zipfile
import py7zr
import rarfile
import tempfile
import json
import sys
import subprocess
from tkinterdnd2 import DND_FILES, TkinterDnD
from xml.etree import ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

I18N = {
    "zh-CN": {
        "app_title": "ModOrganizerPackTranslator",
        "openai_api_key": "OpenAI API Key:",
        "base_url": "Base URL:",
        "model_name": "模型名称:",
        "concurrency": "并发线程数:",
        "ui_language": "界面语言:",
        "target_language": "目标翻译语言:",
        "save_config": "保存配置",
        "drop_here": "请将 .zip, .7z, 或 .rar 文件拖到这里",
        "drop_release": "可以松开鼠标了！",
        "header_title": "ModOrganizerPackTranslator",
        "header_subtitle": "填写 API 配置后，将压缩包拖入下方区域开始处理。",
        "api_section_title": "API 配置",
        "lang_section_title": "语言设置",
        "log_section_title": "处理日志",
        "drop_hint": "支持 .zip、.7z、.rar",
        "processing_error_busy": "错误：正在处理一个文件，请稍后再试。",
        "start_processing_file": "▶️ 开始处理文件: {filename}",
        "warn_invalid_concurrency": "⚠️ 警告: 并发线程数设置无效，已重置为默认值 10。",
        "warn_concurrency_reset": "⚠️ 警告: 并发线程数必须为正整数，已重置为默认值 10。",
        "error_api_key_missing": "❌ 错误: 请输入您的 OpenAI API Key。",
        "create_temp_dir": "  - 创建临时目录: {path}",
        "decompressing": "  - 正在解压: {filename}",
        "error_unsupported_file_type": "❌ 错误: 不支持的文件类型。仅支持 .zip, .7z, .rar",
        "error_decompress_failed": "❌ 错误: 解压文件失败: {error}",
        "sevenzip_fallback": "  - py7zr 不支持该压缩算法，尝试使用 7-Zip...",
        "sevenzip_not_found": "❌ 错误: 未找到 7-Zip (7z/7za/7zr)。请安装 7-Zip 并确保在 PATH 中。",
        "using_extractor": "  - 使用解压工具: {tool}",
        "rar_fallback": "  - rarfile 解压失败，尝试使用外部解压工具...",
        "error_rar_password": "❌ 错误: RAR 文件需要密码，暂不支持解密。",
        "rar_entry_count": "  - RAR 文件包含 {count} 个条目。",
        "rar_extract_progress": "    解压进度: {current}/{total} - {name}",
        "rar_hint": "  - RAR 错误提示: 您可能需要安装 UnRAR 库或将其添加到系统路径中。",
        "searching_moduleconfig": "  - 正在搜索 ModuleConfig.xml...",
        "extracted_structure": "  - 解压后的文件结构:",
        "error_no_moduleconfig": "❌ 错误: 在压缩包中未找到 ModuleConfig.xml。",
        "error_no_moduleconfig_hint": "  - 请检查压缩包是否包含该文件，或文件名是否正确。",
        "found_config": "  - 找到配置文件: {path}",
        "no_texts_to_translate": "✅ 警告: 未在 ModuleConfig.xml 中找到需要翻译的文本。",
        "extracted_texts_count": "  - 提取到 {count} 条待翻译文本。",
        "calling_api": "  - 正在调用 OpenAI API 进行翻译 (并发数: {count})...",
        "translated_success": "    ({index}/{total}) 翻译成功: '{source}' -> '{translated}'",
        "translated_failed": "    ({index}/{total}) ❌ 翻译失败: '{source}', 错误: {error}",
        "translation_summary": "  - 翻译统计: 成功 {success} / 失败 {failed} / 总计 {total}",
        "all_translations_failed_abort": "❌ 所有翻译均失败，可能是 API Key/Base URL/模型配置错误，已取消打包。",
        "no_output_created": "  - 未生成输出压缩包。",
        "translation_failed_fallback": "翻译失败: {text}",
        "updating_xml": "  - 正在用译文更新 XML 文件...",
        "repacking": "  - 正在重新打包为: {filename}",
        "done_output": "✅ 翻译完成！输出文件位于: {path}",
        "fatal_error": "❌ 发生严重错误: {error}",
        "cleanup_temp": "  - 清理临时目录。",
        "cleanup_temp_failed": "  - ❌ 清理临时目录失败: {error}",
        "config_saved": "✅ 配置已保存！",
        "config_save_failed": "❌ 配置保存失败！",
        "config_save_error": "❌ 保存配置时出错: {error}"
    },
    "en": {
        "app_title": "ModOrganizerPackTranslator",
        "openai_api_key": "OpenAI API Key:",
        "base_url": "Base URL:",
        "model_name": "Model:",
        "concurrency": "Concurrency:",
        "ui_language": "UI Language:",
        "target_language": "Target Language:",
        "save_config": "Save",
        "drop_here": "Drop .zip, .7z, or .rar files here",
        "drop_release": "Release to drop!",
        "header_title": "ModOrganizerPackTranslator",
        "header_subtitle": "Configure the API settings, then drop an archive into the area below.",
        "api_section_title": "API Settings",
        "lang_section_title": "Language Settings",
        "log_section_title": "Processing Log",
        "drop_hint": "Supports .zip, .7z, and .rar",
        "processing_error_busy": "Error: A file is being processed. Please try again later.",
        "start_processing_file": "▶️ Processing file: {filename}",
        "warn_invalid_concurrency": "⚠️ Warning: Invalid concurrency value; reset to default 10.",
        "warn_concurrency_reset": "⚠️ Warning: Concurrency must be a positive integer; reset to default 10.",
        "error_api_key_missing": "❌ Error: Please enter your OpenAI API Key.",
        "create_temp_dir": "  - Created temp directory: {path}",
        "decompressing": "  - Decompressing: {filename}",
        "error_unsupported_file_type": "❌ Error: Unsupported file type. Only .zip, .7z, .rar are supported.",
        "error_decompress_failed": "❌ Error: Failed to decompress: {error}",
        "sevenzip_fallback": "  - py7zr doesn't support this compression method; trying 7-Zip...",
        "sevenzip_not_found": "❌ Error: 7-Zip (7z/7za/7zr) not found. Please install 7-Zip and add it to PATH.",
        "using_extractor": "  - Using extractor: {tool}",
        "rar_fallback": "  - rarfile failed; trying external extractor...",
        "error_rar_password": "❌ Error: The RAR file is password-protected; decryption is not supported.",
        "rar_entry_count": "  - RAR contains {count} entries.",
        "rar_extract_progress": "    Extracting: {current}/{total} - {name}",
        "rar_hint": "  - RAR hint: You may need to install UnRAR or add it to PATH.",
        "searching_moduleconfig": "  - Searching for ModuleConfig.xml...",
        "extracted_structure": "  - Extracted file structure:",
        "error_no_moduleconfig": "❌ Error: ModuleConfig.xml not found in the archive.",
        "error_no_moduleconfig_hint": "  - Please check the archive or file name.",
        "found_config": "  - Found config: {path}",
        "no_texts_to_translate": "✅ Warning: No translatable text found in ModuleConfig.xml.",
        "extracted_texts_count": "  - Extracted {count} text entries.",
        "calling_api": "  - Translating with OpenAI API (concurrency: {count})...",
        "translated_success": "    ({index}/{total}) Translated: '{source}' -> '{translated}'",
        "translated_failed": "    ({index}/{total}) ❌ Failed: '{source}', Error: {error}",
        "translation_summary": "  - Translation summary: success {success} / failed {failed} / total {total}",
        "all_translations_failed_abort": "❌ All translations failed. Possible API Key/Base URL/model misconfiguration; repacking cancelled.",
        "no_output_created": "  - No output archive was generated.",
        "translation_failed_fallback": "Translation failed: {text}",
        "updating_xml": "  - Updating XML with translations...",
        "repacking": "  - Repacking to: {filename}",
        "done_output": "✅ Done! Output: {path}",
        "fatal_error": "❌ Fatal error: {error}",
        "cleanup_temp": "  - Cleaned temp directory.",
        "cleanup_temp_failed": "  - ❌ Failed to clean temp directory: {error}",
        "config_saved": "✅ Configuration saved!",
        "config_save_failed": "❌ Failed to save configuration!",
        "config_save_error": "❌ Error while saving configuration: {error}"
    }
}

LANGUAGE_DISPLAY_NAMES = {
    "zh-CN": {"zh-CN": "简体中文", "en": "Simplified Chinese"},
    "zh-TW": {"zh-CN": "繁体中文", "en": "Traditional Chinese"},
    "en": {"zh-CN": "英语", "en": "English"},
    "ja": {"zh-CN": "日语", "en": "Japanese"},
    "ko": {"zh-CN": "韩语", "en": "Korean"},
    "fr": {"zh-CN": "法语", "en": "French"},
    "de": {"zh-CN": "德语", "en": "German"},
    "es": {"zh-CN": "西班牙语", "en": "Spanish"},
    "ru": {"zh-CN": "俄语", "en": "Russian"},
    "it": {"zh-CN": "意大利语", "en": "Italian"},
    "pt-BR": {"zh-CN": "葡萄牙语（巴西）", "en": "Portuguese (Brazil)"}
}

SUPPORTED_UI_LANGUAGES = ["zh-CN", "en"]
SUPPORTED_TARGET_LANGUAGES = list(LANGUAGE_DISPLAY_NAMES.keys())

# --- Helper class to make Customtkinter compatible with TkinterDND2 ---
class CTkinterDnD(ctk.CTk, TkinterDnD.Tk):  # type: ignore
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class App(CTkinterDnD):
    def __init__(self):
        super().__init__()

        self.title("ModOrganizerPackTranslator")
        self.geometry("800x600")
        self.set_window_icon()
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.log_queue = queue.Queue()
        self.processing_lock = threading.Lock()
        
        # 配置文件路径
        self.config_file = "config.json"
        self.default_config = {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model_name": "gpt-4-turbo",
            "concurrency": "10",
            "window_width": 800,
            "window_height": 600,
            "ui_language": "zh-CN",
            "target_language": "zh-CN"
        }
        
        # 加载配置
        self.config = self.load_config()
        
        # 设置窗口大小
        self.geometry(f"{self.config['window_width']}x{self.config['window_height']}")

        self.setup_ui()
        self.setup_dnd()
        self.process_log_queue()
        
        # 绑定窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def t(self, key: str, **kwargs) -> str:
        lang = self.config.get("ui_language", "zh-CN")
        text = I18N.get(lang, I18N.get("en", {})).get(key, I18N.get("en", {}).get(key, key))
        if kwargs and text:
            return text.format(**kwargs)
        return text or key

    def get_language_display_name(self, code):
        ui_lang = self.config.get("ui_language", "zh-CN")
        return LANGUAGE_DISPLAY_NAMES.get(code, {}).get(ui_lang, LANGUAGE_DISPLAY_NAMES.get(code, {}).get("en", code))

    def get_language_option_label(self, code):
        return f"{self.get_language_display_name(code)} ({code})"

    def parse_language_code(self, label):
        if "(" in label and label.endswith(")"):
            return label[label.rfind("(") + 1:-1]
        return label

    def refresh_language_options(self):
        ui_values = [self.get_language_option_label(code) for code in SUPPORTED_UI_LANGUAGES]
        target_values = [self.get_language_option_label(code) for code in SUPPORTED_TARGET_LANGUAGES]
        self.ui_language_menu.configure(values=ui_values)
        self.target_language_menu.configure(values=target_values)
        self.ui_language_var.set(self.get_language_option_label(self.config.get("ui_language", "zh-CN")))
        self.target_language_var.set(self.get_language_option_label(self.config.get("target_language", "zh-CN")))

    def refresh_ui_texts(self):
        self.title(self.t("app_title"))
        self.header_title_label.configure(text=self.t("header_title"))
        self.header_subtitle_label.configure(text=self.t("header_subtitle"))
        self.api_section_title_label.configure(text=self.t("api_section_title"))
        self.lang_section_title_label.configure(text=self.t("lang_section_title"))
        self.log_section_title_label.configure(text=self.t("log_section_title"))
        self.api_key_label.configure(text=self.t("openai_api_key"))
        self.base_url_label.configure(text=self.t("base_url"))
        self.model_name_label.configure(text=self.t("model_name"))
        self.concurrency_label.configure(text=self.t("concurrency"))
        self.ui_language_label.configure(text=self.t("ui_language"))
        self.target_language_label.configure(text=self.t("target_language"))
        self.save_btn.configure(text=self.t("save_config"))
        self.drop_target_label.configure(text=self.t("drop_here"))
        self.drop_hint_label.configure(text=self.t("drop_hint"))
        # 更新placeholder文本
        ui_lang = self.config.get("ui_language", "zh-CN")
        if ui_lang == "zh-CN":
            self.base_url_entry.configure(placeholder_text="例如: https://api.openai.com/v1")
            self.model_name_entry.configure(placeholder_text="例如: gpt-4-turbo")
        else:
            self.base_url_entry.configure(placeholder_text="e.g., https://api.openai.com/v1")
            self.model_name_entry.configure(placeholder_text="e.g., gpt-4-turbo")
        self.refresh_language_options()

    def set_window_icon(self):
        icon_path = resource_path(os.path.join("assets", "icons", "logo.ico"))
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.configure(fg_color=("#f4f6f8", "#1a1d21"))

        top_frame = ctk.CTkFrame(self, corner_radius=14, fg_color=("#ffffff", "#23272f"))
        top_frame.grid(row=0, column=0, padx=18, pady=(18, 12), sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)

        self.header_title_label = ctk.CTkLabel(
            top_frame,
            text=self.t("header_title"),
            font=("Microsoft YaHei UI", 22, "bold"),
            anchor="w"
        )
        self.header_title_label.grid(row=0, column=0, padx=20, pady=(18, 4), sticky="w")

        self.header_subtitle_label = ctk.CTkLabel(
            top_frame,
            text=self.t("header_subtitle"),
            font=("Microsoft YaHei UI", 12),
            text_color=("#5f6b7a", "#b4bdc8"),
            anchor="w"
        )
        self.header_subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="w")

        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)

        settings_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        settings_frame.grid(row=0, column=0, sticky="ew")
        settings_frame.grid_columnconfigure(0, weight=3)
        settings_frame.grid_columnconfigure(1, weight=2)

        api_frame = ctk.CTkFrame(settings_frame, corner_radius=14, fg_color=("#ffffff", "#23272f"))
        api_frame.grid(row=0, column=0, padx=(0, 10), pady=(0, 12), sticky="nsew")
        api_frame.grid_columnconfigure(0, minsize=125)
        api_frame.grid_columnconfigure(1, weight=1)

        self.api_section_title_label = ctk.CTkLabel(
            api_frame,
            text=self.t("api_section_title"),
            font=("Microsoft YaHei UI", 15, "bold"),
            anchor="w"
        )
        self.api_section_title_label.grid(row=0, column=0, columnspan=2, padx=18, pady=(16, 12), sticky="ew")

        self.api_key_label = ctk.CTkLabel(api_frame, text=self.t("openai_api_key"), anchor="w", font=("Microsoft YaHei UI", 12))
        self.api_key_label.grid(row=1, column=0, padx=(18, 12), pady=7, sticky="w")
        self.api_key_entry = ctk.CTkEntry(api_frame, show="*", height=34, corner_radius=8, border_width=1)
        self.api_key_entry.grid(row=1, column=1, padx=(0, 18), pady=7, sticky="ew")
        self.api_key_entry.insert(0, self.config["api_key"])

        self.base_url_label = ctk.CTkLabel(api_frame, text=self.t("base_url"), anchor="w", font=("Microsoft YaHei UI", 12))
        self.base_url_label.grid(row=2, column=0, padx=(18, 12), pady=7, sticky="w")
        self.base_url_entry = ctk.CTkEntry(api_frame, placeholder_text="https://api.openai.com/v1", height=34, corner_radius=8, border_width=1)
        self.base_url_entry.grid(row=2, column=1, padx=(0, 18), pady=7, sticky="ew")
        self.base_url_entry.insert(0, self.config["base_url"])

        self.model_name_label = ctk.CTkLabel(api_frame, text=self.t("model_name"), anchor="w", font=("Microsoft YaHei UI", 12))
        self.model_name_label.grid(row=3, column=0, padx=(18, 12), pady=7, sticky="w")
        self.model_name_entry = ctk.CTkEntry(api_frame, placeholder_text="gpt-4-turbo", height=34, corner_radius=8, border_width=1)
        self.model_name_entry.grid(row=3, column=1, padx=(0, 18), pady=7, sticky="ew")
        self.model_name_entry.insert(0, self.config["model_name"])

        self.concurrency_label = ctk.CTkLabel(api_frame, text=self.t("concurrency"), anchor="w", font=("Microsoft YaHei UI", 12))
        self.concurrency_label.grid(row=4, column=0, padx=(18, 12), pady=(7, 16), sticky="w")
        self.concurrency_entry = ctk.CTkEntry(api_frame, width=120, height=34, corner_radius=8, border_width=1)
        self.concurrency_entry.grid(row=4, column=1, padx=(0, 18), pady=(7, 16), sticky="w")
        self.concurrency_entry.insert(0, self.config["concurrency"])

        side_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        side_frame.grid(row=0, column=1, padx=(10, 0), pady=(0, 12), sticky="nsew")
        side_frame.grid_columnconfigure(0, weight=1)

        lang_frame = ctk.CTkFrame(side_frame, corner_radius=14, fg_color=("#ffffff", "#23272f"))
        lang_frame.grid(row=0, column=0, sticky="ew")
        lang_frame.grid_columnconfigure(0, weight=1)

        self.lang_section_title_label = ctk.CTkLabel(
            lang_frame,
            text=self.t("lang_section_title"),
            font=("Microsoft YaHei UI", 15, "bold"),
            anchor="w"
        )
        self.lang_section_title_label.grid(row=0, column=0, padx=18, pady=(16, 12), sticky="ew")

        self.ui_language_label = ctk.CTkLabel(lang_frame, text=self.t("ui_language"), anchor="w", font=("Microsoft YaHei UI", 12))
        self.ui_language_label.grid(row=1, column=0, padx=18, pady=(0, 6), sticky="w")
        self.ui_language_var = ctk.StringVar(value=self.get_language_option_label(self.config.get("ui_language", "zh-CN")))
        self.ui_language_menu = ctk.CTkOptionMenu(
            lang_frame,
            values=[self.get_language_option_label(code) for code in SUPPORTED_UI_LANGUAGES],
            variable=self.ui_language_var,
            command=self.on_ui_language_change,
            height=34,
            corner_radius=8,
            anchor="w"
        )
        self.ui_language_menu.grid(row=2, column=0, padx=18, pady=(0, 12), sticky="ew")

        self.target_language_label = ctk.CTkLabel(lang_frame, text=self.t("target_language"), anchor="w", font=("Microsoft YaHei UI", 12))
        self.target_language_label.grid(row=3, column=0, padx=18, pady=(0, 6), sticky="w")
        self.target_language_var = ctk.StringVar(value=self.get_language_option_label(self.config.get("target_language", "zh-CN")))
        self.target_language_menu = ctk.CTkOptionMenu(
            lang_frame,
            values=[self.get_language_option_label(code) for code in SUPPORTED_TARGET_LANGUAGES],
            variable=self.target_language_var,
            command=self.on_target_language_change,
            height=34,
            corner_radius=8,
            anchor="w"
        )
        self.target_language_menu.grid(row=4, column=0, padx=18, pady=(0, 16), sticky="ew")

        action_frame = ctk.CTkFrame(side_frame, corner_radius=14, fg_color=("#ffffff", "#23272f"))
        action_frame.grid(row=1, column=0, pady=(12, 0), sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)

        self.save_btn = ctk.CTkButton(
            action_frame,
            text=self.t("save_config"),
            command=self.save_current_config,
            height=38,
            corner_radius=10,
            font=("Microsoft YaHei UI", 13, "bold")
        )
        self.save_btn.grid(row=0, column=0, padx=18, pady=18, sticky="ew")

        log_frame = ctk.CTkFrame(content_frame, corner_radius=14, fg_color=("#ffffff", "#23272f"))
        log_frame.grid(row=1, column=0, sticky="nsew")
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, padx=18, pady=(16, 10), sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)

        self.log_section_title_label = ctk.CTkLabel(
            log_header,
            text=self.t("log_section_title"),
            font=("Microsoft YaHei UI", 15, "bold"),
            anchor="w"
        )
        self.log_section_title_label.grid(row=0, column=0, sticky="w")

        self.drop_hint_label = ctk.CTkLabel(
            log_header,
            text=self.t("drop_hint"),
            font=("Microsoft YaHei UI", 11),
            text_color=("#5f6b7a", "#b4bdc8"),
            anchor="e"
        )
        self.drop_hint_label.grid(row=0, column=1, sticky="e")

        self.log_textbox = ctk.CTkTextbox(
            log_frame,
            state="disabled",
            corner_radius=10,
            border_width=1,
            font=("Consolas", 10),
            wrap="word"
        )
        self.log_textbox.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")

        self.drop_target_label = ctk.CTkLabel(
            self.log_textbox,
            text=self.t("drop_here"),
            font=("Microsoft YaHei UI", 18, "bold"),
            text_color=("#6e7a89", "#a8b0bb")
        )
        self.drop_target_label.place(relx=0.5, rely=0.46, anchor="center")
        
        self.refresh_ui_texts()
        
    def setup_dnd(self):
        self.drop_target_label.drop_target_register(DND_FILES)  # type: ignore
        self.drop_target_label.dnd_bind('<<DropEnter>>', self.drop_enter)  # type: ignore
        self.drop_target_label.dnd_bind('<<DropLeave>>', self.drop_leave)  # type: ignore
        self.drop_target_label.dnd_bind('<<Drop>>', self.drop)  # type: ignore
        self.log_textbox.drop_target_register(DND_FILES)  # type: ignore
        self.log_textbox.dnd_bind('<<Drop>>', self.drop)  # type: ignore

    def on_ui_language_change(self, selected_label):
        code = self.parse_language_code(selected_label)
        if code in SUPPORTED_UI_LANGUAGES:
            self.config["ui_language"] = code
            self.refresh_ui_texts()

    def on_target_language_change(self, selected_label):
        code = self.parse_language_code(selected_label)
        if code in SUPPORTED_TARGET_LANGUAGES:
            self.config["target_language"] = code


    def drop_enter(self, event):
        self.drop_target_label.configure(text=self.t("drop_release"))
        return event.action

    def drop_leave(self, event):
        self.drop_target_label.configure(text=self.t("drop_here"))
        return event.action

    def drop(self, event):
        self.drop_leave(event) # Reset label text
        if self.processing_lock.locked():
            self.log_message(self.t("processing_error_busy"))
            return
            
        filepath = event.data.strip('{}') # Remove braces from filepath
        threading.Thread(target=self.process_file_thread, args=(filepath,)).start()
        return event.action

    def process_log_queue(self):
        try:
            while not self.log_queue.empty():
                message = self.log_queue.get_nowait()
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", message + "\n")
                self.log_textbox.configure(state="disabled")
                self.log_textbox.see("end")
        finally:
            self.after(100, self.process_log_queue)

    def log_message(self, message):
        if hasattr(self, 'drop_target_label') and self.drop_target_label.winfo_exists():
            self.drop_target_label.place_forget()
        self.log_queue.put(message)

    def find_7zip_executable(self):
        for candidate in ("7z", "7za", "7zr"):
            path = shutil.which(candidate)
            if path:
                return path
        return None

    def find_rar_extractor(self):
        unrar_path = shutil.which("unrar")
        if unrar_path:
            return {"type": "unrar", "path": unrar_path}
        winrar_path = shutil.which("WinRAR") or shutil.which("WinRAR.exe")
        if winrar_path:
            return {"type": "winrar", "path": winrar_path}
        sevenzip_path = self.find_7zip_executable()
        if sevenzip_path:
            return {"type": "7z", "path": sevenzip_path}
        return None

    def extract_rar_with_tool(self, filepath, temp_dir, tool_info):
        tool_type = tool_info["type"]
        tool_path = tool_info["path"]
        if tool_type in ("unrar", "winrar"):
            cmd = [tool_path, "x", "-y", filepath, temp_dir]
        elif tool_type == "7z":
            cmd = [tool_path, "x", "-y", f"-o{temp_dir}", filepath]
        else:
            raise RuntimeError("Unknown RAR extractor")
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "RAR extraction failed"
            raise RuntimeError(error_msg)

    def extract_7z_with_7zip(self, filepath, temp_dir):
        exe_path = self.find_7zip_executable()
        if not exe_path:
            raise FileNotFoundError(self.t("sevenzip_not_found"))
        result = subprocess.run(
            [exe_path, "x", "-y", f"-o{temp_dir}", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "7-Zip failed"
            raise RuntimeError(error_msg)

    def process_file_thread(self, filepath):
        if not self.processing_lock.acquire(blocking=False):
            return

        temp_dir = None
        try:
            self.log_message("="*50)
            self.log_message(self.t("start_processing_file", filename=os.path.basename(filepath)))
            
            api_key = self.api_key_entry.get()
            base_url = self.base_url_entry.get()
            model = self.model_name_entry.get()

            try:
                max_workers = int(self.concurrency_entry.get())
                if max_workers <= 0:
                    max_workers = 10
                    self.log_message(self.t("warn_concurrency_reset"))
            except ValueError:
                max_workers = 10
                self.log_message(self.t("warn_invalid_concurrency"))

            if not api_key:
                self.log_message(self.t("error_api_key_missing"))
                return

            client = openai.OpenAI(api_key=api_key, base_url=base_url if base_url else None)

            temp_dir = tempfile.mkdtemp(prefix="mod_translator_")
            self.log_message(self.t("create_temp_dir", path=temp_dir))

            # 1. Decompress archive
            try:
                self.log_message(self.t("decompressing", filename=os.path.basename(filepath)))
                if filepath.endswith('.zip'):
                    with zipfile.ZipFile(filepath, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                elif filepath.endswith('.7z'):
                    try:
                        with py7zr.SevenZipFile(filepath, mode='r') as z:
                            z.extractall(path=temp_dir)
                    except Exception as e:
                        if "BCJ2" in str(e) or "filter is not supported" in str(e):
                            self.log_message(self.t("sevenzip_fallback"))
                            self.extract_7z_with_7zip(filepath, temp_dir)
                        else:
                            raise
                elif filepath.endswith('.rar'):
                    extractor = self.find_rar_extractor()
                    if extractor and extractor["type"] == "unrar":
                        rarfile.UNRAR_TOOL = extractor["path"]
                    try:
                        with rarfile.RarFile(filepath) as rf:
                            if rf.needs_password():
                                self.log_message(self.t("error_rar_password"))
                                return
                            if extractor:
                                self.log_message(self.t("using_extractor", tool=extractor["type"]))
                            rf.extractall(temp_dir)
                    except Exception:
                        if extractor:
                            self.log_message(self.t("rar_fallback"))
                            self.log_message(self.t("using_extractor", tool=extractor["type"]))
                            self.extract_rar_with_tool(filepath, temp_dir, extractor)
                        else:
                            raise
                else:
                    self.log_message(self.t("error_unsupported_file_type"))
                    return
            except Exception as e:
                self.log_message(self.t("error_decompress_failed", error=e))
                if "is not a rar file" in str(e).lower():
                     self.log_message(self.t("rar_hint"))
                return

            # 2. Find and parse ModuleConfig.xml
            config_path = None
            self.log_message(self.t("searching_moduleconfig"))
            
            # 显示解压后的文件结构以便调试
            self.log_message(self.t("extracted_structure"))
            for root, dirs, files in os.walk(temp_dir):
                level = root.replace(temp_dir, '').count(os.sep)
                indent = ' ' * 4 * (level + 1)
                self.log_message(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 4 * (level + 2)
                for file in files:
                    self.log_message(f"{subindent}{file}")
                    if file.lower() == "moduleconfig.xml":
                        config_path = os.path.join(root, file)
                        break
                if config_path:
                    break
            
            if not config_path:
                self.log_message(self.t("error_no_moduleconfig"))
                self.log_message(self.t("error_no_moduleconfig_hint"))
                return

            self.log_message(self.t("found_config", path=os.path.relpath(config_path, temp_dir)))
            
            tree = ET.parse(config_path)
            root = tree.getroot()

            # 3. Extract text for translation
            texts_to_translate = []
            for element in root.findall('.//moduleName') + root.findall('.//description'):
                if element.text and element.text.strip():
                    texts_to_translate.append({'element': element, 'type': 'text', 'original': element.text})

            # Translate specific name attributes that are user-facing
            for element in root.findall('.//installStep[@name]'):
                original_name = element.get('name')
                if original_name and original_name.strip():
                    texts_to_translate.append({'element': element, 'type': 'attrib', 'original': original_name})

            for element in root.findall('.//group[@name]'):
                original_name = element.get('name')
                if original_name and original_name.strip():
                    texts_to_translate.append({'element': element, 'type': 'attrib', 'original': original_name})

            for element in root.findall('.//plugin[@name]'):
                original_name = element.get('name')
                if original_name and original_name.strip():
                    texts_to_translate.append({'element': element, 'type': 'attrib', 'original': original_name})
            
            if not texts_to_translate:
                self.log_message(self.t("no_texts_to_translate"))
                return

            self.log_message(self.t("extracted_texts_count", count=len(texts_to_translate)))
            self.log_message(self.t("calling_api", count=max_workers))

            # 4. Translate concurrently
            translations = {}
            success_count = 0
            failed_count = 0
            total_count = len(texts_to_translate)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_text = {executor.submit(self.translate_text, item['original'], client, model): item for item in texts_to_translate}
                for i, future in enumerate(as_completed(future_to_text)):
                    item = future_to_text[future]
                    try:
                        translated_text = future.result()
                        translations[item['original']] = translated_text
                        success_count += 1
                        self.log_message(self.t("translated_success", index=i+1, total=len(texts_to_translate), source=item['original'], translated=translated_text))
                    except Exception as e:
                        failed_count += 1
                        self.log_message(self.t("translated_failed", index=i+1, total=len(texts_to_translate), source=item['original'], error=e))

            self.log_message(self.t("translation_summary", success=success_count, failed=failed_count, total=total_count))
            if success_count == 0 and failed_count == total_count:
                self.log_message(self.t("all_translations_failed_abort"))
                self.log_message(self.t("no_output_created"))
                return

            # 5. Update XML with translations
            self.log_message(self.t("updating_xml"))
            for item in texts_to_translate:
                translated = translations.get(item['original'])
                if translated is None:
                    continue
                if item['type'] == 'text':
                    item['element'].text = translated
                elif item['type'] == 'attrib':
                    item['element'].set('name', translated)

            # Preserve XML declaration and schema location
            tree.write(config_path, encoding='utf-8', xml_declaration=True)
            
            # Re-insert the schema location because ElementTree doesn't handle it well
            with open(config_path, 'r+', encoding='utf-8') as f:
                content = f.read()
                f.seek(0, 0)
                # This is a bit of a hack but robust for this specific XML structure
                content = content.replace('<config>', '<config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">', 1)
                f.write(content)

            # 6. Repack archive
            output_filename = os.path.splitext(os.path.basename(filepath))[0] + "_translated.zip"
            output_path = os.path.join(os.path.dirname(filepath), output_filename)
            self.log_message(self.t("repacking", filename=output_filename))
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root_dir, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root_dir, file)
                        archive_path = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, archive_path)

            self.log_message(self.t("done_output", path=output_path))

        except Exception as e:
            self.log_message(self.t("fatal_error", error=e))
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    self.log_message(self.t("cleanup_temp"))
                except OSError as e:
                    self.log_message(self.t("cleanup_temp_failed", error=e))
            self.processing_lock.release()

    def translate_text(self, text, client, model):
        try:
            target_code = self.config.get("target_language", "zh-CN")
            target_language_name = LANGUAGE_DISPLAY_NAMES.get(target_code, {}).get("en", target_code)
            system_prompt = f"""You are a professional translator for game mods. Your task is to translate input text into {target_language_name}.

Rules:
1. Accuracy and naturalness: translations should read naturally and fit game context.
2. Clean output: return only the translated text, no explanations or extra content.
3. Preserve formatting: keep all special characters, HTML tags (e.g., <br>), brackets, and quotes.
4. Terminology:
   - Keep proper nouns (names, places, skills) in their original form unless a standard localized form exists.
   - Use commonly accepted translations for game terms.
   - Keep technical terms accurate.
5. Context: text comes from Mod Organizer 2 installation config, including module names and descriptions.

Style: concise and clear for players."""

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Translate the following text into {target_language_name}: {text}"}
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {e}")

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置，确保所有必需的键都存在
                merged_config = self.default_config.copy()
                merged_config.update(config)
                print(f"✅ 已加载配置文件: {self.config_file}")
                return merged_config
            else:
                # 首次运行，创建默认配置文件
                self.save_config_silent(self.default_config)
                print(f"📄 已创建默认配置文件: {self.config_file}")
                return self.default_config.copy()
        except Exception as e:
            print(f"⚠️ 配置文件加载失败，使用默认配置: {e}")
            return self.default_config.copy()

    def save_config_silent(self, config):
        """静默保存配置到文件（启动时使用）"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ 配置保存失败: {e}")
            return False

    def save_config(self, config):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.log_message(f"❌ 配置保存失败: {e}")
            return False

    def save_current_config(self):
        """保存当前界面的配置"""
        try:
            # 获取当前窗口大小
            current_geometry = self.geometry()
            if not current_geometry:
                current_geometry = "800x600+0+0"
            width, height = current_geometry.split('x')[0], current_geometry.split('x')[1].split('+')[0]
            
            current_config = {
                "api_key": self.api_key_entry.get(),
                "base_url": self.base_url_entry.get(),
                "model_name": self.model_name_entry.get(),
                "concurrency": self.concurrency_entry.get(),
                "window_width": int(width),
                "window_height": int(height),
                "ui_language": self.parse_language_code(self.ui_language_var.get()),
                "target_language": self.parse_language_code(self.target_language_var.get())
            }
            
            if self.save_config(current_config):
                self.config = current_config
                self.refresh_ui_texts()
                self.log_message(self.t("config_saved"))
            else:
                self.log_message(self.t("config_save_failed"))
        except Exception as e:
            self.log_message(self.t("config_save_error", error=e))

    def on_closing(self):
        """程序关闭时自动保存配置"""
        self.save_current_config()
        self.destroy()


if __name__ == "__main__":
    # On Windows, we might need to tell rarfile where to find the unrar executable
    # You can bundle it with your app or ask the user to install it.
    # Example: rarfile.UNRAR_TOOL = "path/to/unrar.exe"
    app = App()
    app.mainloop() 
