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
from tkinterdnd2 import DND_FILES, TkinterDnD
from xml.etree import ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Helper class to make Customtkinter compatible with TkinterDND2 ---
class CTkinterDnD(ctk.CTk, TkinterDnD.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class App(CTkinterDnD):
    def __init__(self):
        super().__init__()

        self.title("Mod安装包翻译工具")
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
            "window_height": 600
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

        # --- OpenAI Settings Frame ---
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(settings_frame, text="OpenAI API Key:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.api_key_entry = ctk.CTkEntry(settings_frame, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.api_key_entry.insert(0, self.config["api_key"])

        ctk.CTkLabel(settings_frame, text="Base URL:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.base_url_entry = ctk.CTkEntry(settings_frame, placeholder_text="例如: https://api.openai.com/v1")
        self.base_url_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.base_url_entry.insert(0, self.config["base_url"])

        ctk.CTkLabel(settings_frame, text="模型名称:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.model_name_entry = ctk.CTkEntry(settings_frame, placeholder_text="例如: gpt-4-turbo")
        self.model_name_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.model_name_entry.insert(0, self.config["model_name"])

        ctk.CTkLabel(settings_frame, text="并发线程数:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.concurrency_entry = ctk.CTkEntry(settings_frame)
        self.concurrency_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        self.concurrency_entry.insert(0, self.config["concurrency"])

        # 保存配置按钮
        save_btn = ctk.CTkButton(settings_frame, text="保存配置", command=self.save_current_config, width=100)
        save_btn.grid(row=4, column=1, padx=10, pady=5, sticky="e")

        # --- Log and Drop Frame ---
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled", corner_radius=0)
        self.log_textbox.grid(row=0, column=0, sticky="nsew")

        self.drop_target_label = ctk.CTkLabel(self.log_textbox, text="请将 .zip, .7z, 或 .rar 文件拖到这里", font=("", 20))
        self.drop_target_label.place(relx=0.5, rely=0.5, anchor="center")
        
    def setup_dnd(self):
        self.drop_target_label.drop_target_register(DND_FILES)
        self.drop_target_label.dnd_bind('<<DropEnter>>', self.drop_enter)
        self.drop_target_label.dnd_bind('<<DropLeave>>', self.drop_leave)
        self.drop_target_label.dnd_bind('<<Drop>>', self.drop)
        self.log_textbox.drop_target_register(DND_FILES)
        self.log_textbox.dnd_bind('<<Drop>>', self.drop)


    def drop_enter(self, event):
        self.drop_target_label.configure(text="可以松开鼠标了！")
        return event.action

    def drop_leave(self, event):
        self.drop_target_label.configure(text="请将 .zip, .7z, 或 .rar 文件拖到这里")
        return event.action

    def drop(self, event):
        self.drop_leave(event) # Reset label text
        if self.processing_lock.locked():
            self.log_message("错误：正在处理一个文件，请稍后再试。")
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

    def process_file_thread(self, filepath):
        if not self.processing_lock.acquire(blocking=False):
            return

        try:
            self.log_message("="*50)
            self.log_message(f"▶️ 开始处理文件: {os.path.basename(filepath)}")
            
            api_key = self.api_key_entry.get()
            base_url = self.base_url_entry.get()
            model = self.model_name_entry.get()

            try:
                max_workers = int(self.concurrency_entry.get())
                if max_workers <= 0:
                    max_workers = 10
                    self.log_message("⚠️ 警告: 并发线程数必须为正整数，已重置为默认值 10。")
            except ValueError:
                max_workers = 10
                self.log_message("⚠️ 警告: 并发线程数设置无效，已重置为默认值 10。")

            if not api_key:
                self.log_message("❌ 错误: 请输入您的 OpenAI API Key。")
                return

            client = openai.OpenAI(api_key=api_key, base_url=base_url if base_url else None)

            temp_dir = tempfile.mkdtemp(prefix="mod_translator_")
            self.log_message(f"  - 创建临时目录: {temp_dir}")

            # 1. Decompress archive
            try:
                self.log_message(f"  - 正在解压: {os.path.basename(filepath)}")
                if filepath.endswith('.zip'):
                    with zipfile.ZipFile(filepath, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                elif filepath.endswith('.7z'):
                    with py7zr.SevenZipFile(filepath, mode='r') as z:
                        z.extractall(path=temp_dir)
                elif filepath.endswith('.rar'):
                    with rarfile.RarFile(filepath) as rf:
                        rf.extractall(temp_dir)
                else:
                    self.log_message("❌ 错误: 不支持的文件类型。仅支持 .zip, .7z, .rar")
                    return
            except Exception as e:
                self.log_message(f"❌ 错误: 解压文件失败: {e}")
                if "is not a rar file" in str(e).lower():
                     self.log_message("  - RAR 错误提示: 您可能需要安装 UnRAR 库或将其添加到系统路径中。")
                return

            # 2. Find and parse ModuleConfig.xml
            config_path = None
            self.log_message(f"  - 正在搜索 ModuleConfig.xml...")
            
            # 显示解压后的文件结构以便调试
            self.log_message(f"  - 解压后的文件结构:")
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
                self.log_message("❌ 错误: 在压缩包中未找到 ModuleConfig.xml。")
                self.log_message("  - 请检查压缩包是否包含该文件，或文件名是否正确。")
                return

            self.log_message(f"  - 找到配置文件: {os.path.relpath(config_path, temp_dir)}")
            
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
                self.log_message("✅ 警告: 未在 ModuleConfig.xml 中找到需要翻译的文本。")
                return

            self.log_message(f"  - 提取到 {len(texts_to_translate)} 条待翻译文本。")
            self.log_message(f"  - 正在调用 OpenAI API 进行翻译 (并发数: {max_workers})...")

            # 4. Translate concurrently
            translations = {}
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_text = {executor.submit(self.translate_text, item['original'], client, model): item for item in texts_to_translate}
                for i, future in enumerate(as_completed(future_to_text)):
                    item = future_to_text[future]
                    try:
                        translated_text = future.result()
                        translations[item['original']] = translated_text
                        self.log_message(f"    ({i+1}/{len(texts_to_translate)}) 翻译成功: '{item['original']}' -> '{translated_text}'")
                    except Exception as e:
                        self.log_message(f"    ({i+1}/{len(texts_to_translate)}) ❌ 翻译失败: '{item['original']}', 错误: {e}")
                        translations[item['original']] = f"翻译失败: {item['original']}"

            # 5. Update XML with translations
            self.log_message("  - 正在用译文更新 XML 文件...")
            for item in texts_to_translate:
                translated = translations.get(item['original'], item['original'])
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
            self.log_message(f"  - 正在重新打包为: {output_filename}")
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root_dir, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root_dir, file)
                        archive_path = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, archive_path)

            self.log_message(f"✅ 翻译完成！输出文件位于: {output_path}")

        except Exception as e:
            self.log_message(f"❌ 发生严重错误: {e}")
        finally:
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    self.log_message(f"  - 清理临时目录。")
                except OSError as e:
                    self.log_message(f"  - ❌ 清理临时目录失败: {e}")
            self.processing_lock.release()

    def translate_text(self, text, client, model):
        try:
            system_prompt = """你是一名专门翻译游戏Mod的专业译者。你的任务是将英文文本翻译成简体中文。

翻译规则：
1. 准确性和自然度：翻译应当流畅自然，符合中文表达习惯，贴合游戏语境
2. 纯净输出：只返回翻译后的中文文本，不要包含原文、解释或其他无关内容
3. 保持格式：保留所有特殊字符、HTML标签（如 `<br>`）、括号、引号等格式，这些对游戏引擎很重要
4. 术语处理：
   - 保留专有名词的英文原文（如人名、地名、技能名等）
   - 常见游戏术语使用约定俗成的中文翻译
   - 技术性词汇保持准确性
5. 语境说明：文本来自Mod Organizer 2的安装配置文件，包含模组名称和功能描述

翻译风格：简洁明了，适合中文游戏玩家阅读。"""

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请翻译以下文本：{text}"}
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
            width, height = current_geometry.split('x')[0], current_geometry.split('x')[1].split('+')[0]
            
            current_config = {
                "api_key": self.api_key_entry.get(),
                "base_url": self.base_url_entry.get(),
                "model_name": self.model_name_entry.get(),
                "concurrency": self.concurrency_entry.get(),
                "window_width": int(width),
                "window_height": int(height)
            }
            
            if self.save_config(current_config):
                self.config = current_config
                self.log_message("✅ 配置已保存！")
            else:
                self.log_message("❌ 配置保存失败！")
        except Exception as e:
            self.log_message(f"❌ 保存配置时出错: {e}")

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