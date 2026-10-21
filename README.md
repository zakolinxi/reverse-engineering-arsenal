# Reverse Engineering Arsenal

把 41 个逆向工程来源融合成一个可路由的 AI 技能：**Electron/桌面、Web JS、网络抓包、指纹浏览器、原生二进制、Android/iOS、学习资源**，每个领域都有独立参考、可执行脚本和上游工具目录。

> 仅用于你拥有或获得明确授权的目标：自有系统、CTF、恶意软件防御分析、合约安全测试、允许的互操作研究。禁止未授权访问、窃取凭据、绕过付费/许可/访问控制、欺诈或投放恶意软件。

## 为什么是“一个技能”

- **单入口**：`SKILL.md` 负责授权检查、任务路由、统一证据流程和跨领域作战手册。
- **不丢能力**：`assets/upstream-catalog.json` 记录全部 41 个来源的 URL、能力、安装方式与参考位置；`references/source-coverage.md` 逐项证明覆盖关系。
- **可落地**：不硬拷第三方源码（许可证/体积/维护不现实），内置 6 个原创脚本，并可按需浅克隆上游完整实现。
- **证据优先**：先静态分诊、再动态取证、定位 writer/sink、还原算法，最后用真实样本验证。

## 能力范围

| 领域 | 参考文档 | 代表能力 |
| --- | --- | --- |
| Electron / 桌面 | [electron-desktop.md](references/electron-desktop.md) | ASAR、CDP 主/渲染调试、fuses、`.jsc`、`.node`、Frida、IPC/登录态案例 |
| Web / JavaScript | [js-web-reverse.md](references/js-web-reverse.md) | 请求链、断点、Hook、AST 去混淆、JSVMP/WASM、RuyiTrace、Firefox-Reverse |
| 网络拦截 | [network-capture.md](references/network-capture.md) | mitmproxy、MiteProxy、mitmproxy-mcp、证书、WebSocket、Android/iOS 真机 |
| 指纹与反检测 | [browser-fingerprint.md](references/browser-fingerprint.md) | VirtualBrowser、Luna、Firefox/Ruyi 系、检测站、TideFinger 资产指纹 |
| 原生二进制 | [native-binary.md](references/native-binary.md) | Ghidra、DIE、x64dbg、PE patch、PyInstaller、VMProtect/加壳 |
| Android / iOS | [mobile-android-ios.md](references/mobile-android-ios.md) | jadx/apktool、Frida 加密 Hook、脱壳、So/native、iOS 工具链 |
| 学习资源 | [awesome-learning.md](references/awesome-learning.md) | 6 份 awesome 列表、工具短名单、12 周路径 |

## 目录结构

```text
reverse-engineering-arsenal/
├── SKILL.md                     # 技能入口：路由 + 工作流 + 安全边界
├── assets/
│   └── upstream-catalog.json    # 41 个来源的机器可读目录
├── references/
│   ├── electron-desktop.md
│   ├── js-web-reverse.md
│   ├── network-capture.md
│   ├── browser-fingerprint.md
│   ├── native-binary.md
│   ├── mobile-android-ios.md
│   ├── awesome-learning.md
│   └── source-coverage.md       # 来源覆盖矩阵（41/41）
└── scripts/
    ├── env_probe.py             # 工具链探测
    ├── asar_tool.py             # 纯 Python ASAR 列表/提取/校验
    ├── js_triage.py             # JS 混淆/加密/端点分诊
    ├── hook_gen.py              # 生成 fetch/XHR/WS/Cookie/Crypto Hook
    ├── mitm_capture.py          # mitmproxy JSONL 抓包 addon
    └── fetch_upstream.py        # 浏览/检查/浅克隆上游
```

## 安装为技能

任选一个技能目录：

```bash
git clone <repo-url> ~/.agents/skills/reverse-engineering-arsenal
# 或
git clone <repo-url> ~/.claude/skills/reverse-engineering-arsenal
# 或项目级
git clone <repo-url> .qoder/skills/reverse-engineering-arsenal
```

重启会话或运行 `/skills reload`，然后直接说“逆向这个站点/分析这个 Electron 应用/抓包”，或显式调用 `/reverse-engineering-arsenal`。

## 快速使用

```bash
# 环境探测
python scripts/env_probe.py

# ASAR
python scripts/asar_tool.py list app.asar
python scripts/asar_tool.py info app.asar
python scripts/asar_tool.py extract app.asar out/ --verify

# JS 分诊
python scripts/js_triage.py bundle.js --out triage.md

# 生成运行时 Hook
python scripts/hook_gen.py --type all --out hooks.js
node --check hooks.js

# mitmproxy 取证
RE_CAPTURE_OUT=flows.jsonl mitmdump -q -p 8888 -s scripts/mitm_capture.py

# 浏览/获取上游
python scripts/fetch_upstream.py list
python scripts/fetch_upstream.py check --limit 5
python scripts/fetch_upstream.py fetch js-reverse-mcp --dest ./upstream
```

## 41 个来源的特殊处理

- **RuyiTrace**：原 `LoseNine/Firefox-FingerPrint-Analyzer` 已 404；其能力、开关手册与采集脚本由同源的 `erma0/js-reverse-skill` 完整保留。
- **re-electron**：skills.rest 展示页指向真实源仓库 `dslsdzc/rev-skills`。
- **Exe-Decompiler**：闭源商业工具，README/参考中给出开源等价链路。
- **PE-reverse-skill**：仅保留合法逆向能力；其面向大模型的 jailbreak/指令注入组件被明确排除。
- 全部来源、许可证提示与覆盖位置见 [source-coverage.md](references/source-coverage.md) 和 [upstream-catalog.json](assets/upstream-catalog.json)。

## 已验证

- 在真实 151MB Electron `app.asar` 上完成列表、单文件提取、SHA-256 校验、`app.asar.unpacked` 提取。
- JS 分诊在真实混淆样本上输出正确分类。
- 全部 Hook 类型通过 `node --check`。
- mitmdump + 本地 HTTP 服务端到端抓包成功。
- 41/41 来源覆盖、无 TODO、主文档 <500 行、目录内链接有效。

GUI/商业工具（Ghidra、x64dbg、VirtualBrowser、Firefox-Reverse 等）需按参考文档自行安装，本仓库不包含其二进制。

## 上游与许可

本仓库只包含原创文档与脚本，不重新分发第三方代码。各上游项目许可证不同，使用/分发前请逐一核对；引用链接与能力说明不构成对其授权。当前仓库未附加 LICENSE，默认保留所有权利；如需开源请自行添加合适的许可证。

## 安全与合规

- 只在授权范围内操作；动态分析使用隔离 VM/快照，未知样本默认断网。
- 报告脱敏：token、Cookie、密钥、用户数据不得写入交付物。
- 指纹浏览器/反检测仅用于隐私、多账号管理、授权研究；不用于欺诈或平台条款禁止的行为。
- 不提供破解许可/DRM、未授权访问或恶意软件的教程。
