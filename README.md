# ModOrganizerPackTranslator

一个用于翻译 Mod Organizer 安装包的工具，支持自动翻译 `.zip`、`.7z` 和 `.rar` 格式的 Mod 安装包。

## 功能特性

- 🎯 **智能翻译**: 使用 OpenAI GPT 模型自动翻译 Mod 描述和说明
- 📦 **多格式支持**: 支持 `.zip`、`.7z`、`.rar` 压缩包格式
- 🖱️ **拖拽操作**: 简单直观的拖拽界面，无需复杂操作
- ⚡ **并发处理**: 支持多线程并发翻译，提高处理效率
- 💾 **配置保存**: 自动保存 API 配置，无需重复输入
- 🎨 **现代界面**: 基于 CustomTkinter 的现代化用户界面

## 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.7 或更高版本
- **内存**: 建议 4GB 或更多
- **网络**: 需要稳定的网络连接以访问 OpenAI API

## 安装说明

### 方法一：使用预编译版本（推荐）

1. 从 [Releases](https://github.com/fqscfqj/ModOrganizerPackTranslator/releases) 页面下载最新版本的 `ModTranslator.exe`
2. 直接运行可执行文件，无需安装 Python 环境

### 方法二：从源码运行

1. **克隆仓库**
   ```bash
   git clone https://github.com/fqscfqj/ModOrganizerPackTranslator.git
   cd ModOrganizerPackTranslator
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行程序**
   ```bash
   python main.py
   ```

### 方法三：自行编译

1. 按照方法二安装依赖
2. 运行编译脚本：
   ```bash
   build.bat
   ```
3. 编译完成后，可执行文件将位于 `dist/ModTranslator.exe`

## 使用说明

### 首次使用

1. **获取 OpenAI API Key**
   - 访问 [OpenAI Platform](https://platform.openai.com/api-keys)
   - 创建新的 API Key
   - 复制 API Key

2. **配置程序**
   - 启动程序
   - 在设置区域输入您的 OpenAI API Key
   - 可选择自定义 Base URL 和模型名称
   - 点击"保存配置"按钮

### 翻译 Mod 安装包

1. **准备文件**
   - 确保您有要翻译的 Mod 安装包（`.zip`、`.7z` 或 `.rar` 格式）
   - 安装包应包含 `ModuleConfig.xml` 文件

2. **开始翻译**
   - 将 Mod 安装包文件拖拽到程序窗口
   - 程序将自动解压并分析文件结构
   - 翻译过程将在日志区域显示进度

3. **获取结果**
   - 翻译完成后，程序会在原文件同目录下创建翻译后的文件
   - 文件名格式：`原文件名_翻译版.原扩展名`

## 配置选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| API Key | OpenAI API 密钥 | 必填 |
| Base URL | API 基础地址 | `https://api.openai.com/v1` |
| 模型名称 | 使用的 GPT 模型 | `gpt-4-turbo` |
| 并发线程数 | 同时处理的翻译任务数 | `10` |

## 支持的 Mod 格式

程序专门为 Mod Organizer 设计的安装包格式优化，支持：

- **ModuleConfig.xml**: 自动识别和翻译 Mod 描述
- **多语言支持**: 自动检测原文语言并翻译为中文
- **保持格式**: 翻译过程中保持原有的 XML 结构和格式

## 注意事项

⚠️ **重要提醒**：

1. **API 费用**: 使用 OpenAI API 会产生费用，请确保您的账户有足够的余额
2. **网络连接**: 翻译过程需要稳定的网络连接
3. **文件备份**: 建议在翻译前备份原始文件
4. **RAR 支持**: 如需处理 RAR 文件，可能需要安装 UnRAR 库

## 故障排除

### 常见问题

**Q: 程序无法启动**
- 确保已安装 Python 3.7+ 和所有依赖包
- 检查是否有防火墙或杀毒软件阻止

**Q: 翻译失败**
- 检查 API Key 是否正确
- 确认网络连接正常
- 查看日志区域的错误信息

**Q: RAR 文件无法解压**
- 安装 UnRAR 库：`pip install unrar`
- 或将 UnRAR 可执行文件添加到系统 PATH

**Q: 翻译质量不理想**
- 尝试使用更高级的模型（如 gpt-4）
- 检查原文是否清晰完整

## 开发信息

### 技术栈

- **GUI 框架**: CustomTkinter + TkinterDnD2
- **AI 服务**: OpenAI GPT API
- **压缩格式**: zipfile, py7zr, rarfile
- **打包工具**: PyInstaller

### 项目结构

```
ModOrganizerPackTranslator/
├── main.py              # 主程序文件
├── requirements.txt     # Python 依赖
├── assets/
│   └── icons/
│       ├── logo.ico      # 程序图标
│       └── logo.png      # 程序图标（PNG）
├── build.bat           # 编译脚本
└── README.md           # 说明文档
```

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送分支：`git push origin feature/AmazingFeature`
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本的 Mod 安装包翻译功能
- 图形化用户界面
- 拖拽操作支持