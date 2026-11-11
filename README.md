# dsh-icons

**把 [vscode-icons](https://github.com/vscode-icons/vscode-icons) 带到 DSH 原生文件树。**

[![Validate](https://github.com/simonguo/dsh-icons/actions/workflows/ci.yml/badge.svg)](https://github.com/simonguo/dsh-icons/actions/workflows/ci.yml)
[![Sync vscode-icons](https://github.com/simonguo/dsh-icons/actions/workflows/sync-icons.yml/badge.svg)](https://github.com/simonguo/dsh-icons/actions/workflows/sync-icons.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

不另造一个文件浏览器，也不改 DSH 安装目录。开启插件后，现有文件树里的文件和文件夹直接使用 vscode-icons；关闭插件即可恢复原来的图标。

## 功能

- **原生覆盖**：作用于 DSH「文件」页和文件预览旁复用的目录树。
- **完整本地图标集**：随插件携带官方发布包内全部 SVG，无 CDN、无图标请求到第三方服务器。
- **上游关联规则**：按文件名、复合扩展名、扩展名与文件夹名选择图标；文件夹支持展开与收起两种状态。
- **保留原生交互**：展开目录、打开文件、右键菜单、文件预览与访问权限仍由 DSH 管理。
- **可撤销**：插件卸载时样式随生命周期清理，不修改文件内容。

当前固定的上游版本为 **v13.0.0**：1,664 个 SVG，1,923 条文件名规则、599 条扩展名规则、524 条文件夹名规则。准确版本、发布包来源和 SHA-256 见 [`vendor/upstream.json`](vendor/upstream.json)，生成统计见 [`icon-stats.json`](icon-stats.json)。

## 安装

### 从源码安装

```bash
git clone https://github.com/simonguo/dsh-icons.git
cd dsh-icons
```

仓库已经包含可运行的客户端产物与图标，**安装插件不需要 npm install，也不需要构建**。

在 DSH 中让插件管理工具安装这个目录即可。例如对 DSH 助手说：

> 使用 Plugin Manager 安装我刚克隆的 dsh-icons 本地目录，并启用。

或通过 `plugin_manager` 调用：

```json
{
  "action": "install_bundle",
  "target": "/absolute/path/to/dsh-icons"
}
```

本地目录安装是链接安装，请保留克隆目录。开启后查看原有「文件」页；没有新的「文件图标」面板要寻找。如果当前页面没有收到热加载，刷新 DSH 页面。需要恢复默认图标时，在插件管理中关闭 **dsh-icons**。

> GitHub 开源不等于已发布到 npm 或插件市场。这里的安装说明采用本地目录方式。

## 如何实现

当前 DSH 没有单独的文件树图标扩展点。插件通过 Cordis 的 `shell.overlay` 注册一个只输出 `<style>` 的组件，使用原生文件树的 `data-files-entry` 与 `data-files-path` 语义标记进行匹配：

1. 隐藏当前行中的原生 SVG 图标。
2. 使用伪元素呈现本地 vscode-icons 资源。
3. 由原生按钮的 `aria-expanded` 决定文件夹展开图标。

资源 URL 通过 DSH 的 `require.asset` 解析，适配 Web 与桌面资源载体。没有 DOM 扫描、MutationObserver、轮询、文件系统扫描或新 RPC；插件不接管文件树组件。

匹配优先级：**具体文件名 > 长复合扩展名 > 短扩展名 > 默认图标**。规则忽略大小写。

### 性能

原始实现为每条关联重复生成深层选择器和浅色规则，客户端产物约 2.36 MB。整理后的实现：

- 关联规则只匹配文件树 `li` 行，只有三条结构规则处理子元素和展开状态。
- 合并文件夹展开/收起映射，不重复生成整套浅色样式。
- 每个唯一资源 URL 只解析一次。
- 复用稳定的 style React 元素，避免无关渲染重复构造整段 CSS。

固定上游版本下，客户端产物缩小至约 **602 KB（减少约 75%）**，CSS 规则为 **3,103 条**。这是产物与结构指标，**不是滚动帧率基准**；仍保留几千条文件名规则，超大目录下可能有样式匹配成本。

若文件树卡顿，先在同一个目录中关闭/开启插件作 A/B 比较；目录读取、原生树渲染和图标样式的成本需要分开判断。欢迎提交 DSH 版本、可见行数、复现步骤与浏览器 Performance 记录。不要提交敏感路径或文件内容。

## 兼容性与边界

- 已在 DSH `0.2.2-rc.1` 系列桌面环境验证原生覆盖；其他版本尚未逐一验证。
- 依赖原生行语义标记与内部层级；DSH 改动文件树后可能需要适配。
- 只覆盖文件树行，不宣称覆盖聊天附件、文件标签栏、目录选择器等所有文件图标。
- 不读取项目内容，因此不提供 vscode-icons 在 VS Code 中基于语言 ID、项目检测或用户配置的完整行为。
- 所有上游图标都打包，但并非所有图标都有文件名规则可触发。
- 当前使用标准图标集；浅色专用资源保留在包内，但未自动切换。
- 在一个 DSH Profile 中安装会作用于该 Profile 的会话，不是仅当前聊天。

## 开发

需要 Python **3.9+**（仅标准库）和 Node.js **22+**（语法检查）。同步脚本需要 Python **3.9+** 和网络访问 GitHub。

```bash
# 用已固定的上游映射重建，不联网
python3 scripts/build.py

# 资源、映射、许可证和生成一致性校验
python3 scripts/check.py
node --check client.js
node --check index.js

# 检查实际 npm 分发文件，不会发布
npm pack --dry-run

# 同步最新官方发布包，然后重建
python3 scripts/sync_upstream.py
python3 scripts/build.py

# 或重现指定版本
python3 scripts/sync_upstream.py --tag v13.0.0
python3 scripts/build.py
```

同步时只读取官方 VSIX 的 SVG、主题映射和许可证，**不安装或执行上游扩展代码**。下载临时数据仅保存在内存，不把 VSIX、源码压缩包或完整上游仓库提交到本仓库。

### 项目结构

```text
assets/                     完整上游 SVG 图标集
src/client.template.js      客户端模块模板
scripts/build.py            确定性生成客户端模块
scripts/sync_upstream.py    下载官方发布包并更新资源
scripts/check.py            资源与生成产物校验
vendor/                     上游映射、许可证、版本与校验和
.github/workflows/          CI 与定期同步 PR
client.js                   已生成、可直接安装的客户端产物
index.js                    空 Host 半，不注册额外服务
cordis.patch.yml            Cordis bundle 入口
locale/                     插件列表的中英文元信息
```

## 自动同步 vscode-icons

[Sync vscode-icons](.github/workflows/sync-icons.yml) 每周一 **02:17 UTC / 北京时间 10:17** 检查最新正式发布包，也支持手动指定 tag。

工作流会下载完整资源、更新来源校验和、重新生成客户端并校验，然后创建或更新 `chore/sync-vscode-icons` 分支的 **Pull Request**。**不会自动合并，也不会自动发布 npm 包。** 无新版本且生成内容不变时不创建提交。

首次启用需要仓库允许 Actions 写入内容及创建 Pull Request（Settings → Actions → General → Workflow permissions）。GitHub 对长期不活跃公开仓库可能暂停定时工作流，维护者可手动重新启用。Actions 的定时执行可能延迟。

## 贡献

反馈问题请附 DSH 版本、系统、出问题的文件名模式和可复现步骤。修改模板或生成器后，请重建 `client.js` 并运行校验；不要手改生成产物。请勿提交本机日志、用户截图、个人路径、VSIX、压缩包或 node_modules。

## 致谢与许可

- 图标与关联规则来自 [vscode-icons/vscode-icons](https://github.com/vscode-icons/vscode-icons)，感谢上游维护者与贡献者。
- 插件代码采用 [MIT](LICENSE) 许可证。
- 上游图标与映射保留其 [原始 MIT 许可证](vendor/LICENSE.vscode-icons.txt)。品牌图形及商标属于各自权利人；本项目不代表 DSH、vscode-icons 或相关品牌的官方背书。
