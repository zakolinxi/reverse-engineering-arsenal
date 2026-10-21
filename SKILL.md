---
name: reverse-engineering-arsenal
description: "统一的逆向工程技能库，覆盖 Electron/asar/CDP、Web JavaScript 反混淆与 JSVMP/WASM、mitmproxy/MiteProxy 抓包、指纹浏览器与反检测、Ghidra/x64dbg/PE/PyInstaller/VMProtect、Android/iOS/Frida、TideFinger 识别及全套资源清单。当用户要求逆向、反混淆、脱壳、抓包、分析签名/token/Cookie/设备指纹、调试 Electron/APK/EXE/ELF、还原算法、构建指纹环境或查找逆向工具时使用。Triggers: reverse engineering, deobfuscation, asar, Electron, CDP, mitmproxy, JSVMP, WASM, Frida, Ghidra, x64dbg, Android, APK, PE, VMP, PyInstaller, fingerprint browser, 逆向, 反混淆, 脱壳, 抓包, 指纹浏览器, 协议还原."
---

# Reverse Engineering Arsenal

一个把 41 个逆向来源融合成单一路由的技能：静态分诊 → 动态取证 → 写边界定位 → 算法/环境还原 → 真实请求验证 → 可复现交付。

## 1. 授权与安全边界（每次必须先确认）

- 
- 报告中脱敏：token、Cookie、Authorization、密钥、手机号、身份证、代理账号、客户数据。

## 2. 能力地图

| 领域            | 参考                                  | 核心来源/工具                                                                                                      |
| ------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Electron / 桌面 | `references/electron-desktop.md`    | @electron/asar、re-electron、Frida、electron-dev-tools、MiniMax 案例                                               |
| Web / JS      | `references/js-web-reverse.md`      | js-reverse-mcp、jshook、hello_js_reverse_skill、js-reverse-skill、js-deobfuscator、RuyiTrace、Firefox-Reverse、REOT |
| 网络拦截          | `references/network-capture.md`     | mitmproxy、MiteProxy、mitmproxy-mcp、证书/WS/真机抓包                                                                 |
| 指纹与反检测        | `references/browser-fingerprint.md` | VirtualBrowser、Luna、Firefox/Ruyi 系、TideFinger_Go、浏览器资源地图                                                     |
| 原生二进制         | `references/native-binary.md`       | Ghidra、DIE、x64dbg、awesome-vmp、PyInstaller、PE Reverse Analyzer                                                |
| Android / iOS | `references/mobile-android-ios.md`  | jadx/apktool/Frida、RxAppEncryptionProtocol、Android 工具索引、iOS 工具索引                                             |
| 学习与资源         | `references/awesome-learning.md`    | 6 份 awesome 列表、12 周路径、工具短名单                                                                                  |
| 来源覆盖          | `references/source-coverage.md`     | 41/41 来源 → 能力 → 参考位置对照表                                                                                      |

## 3. 60 秒路由

先判定输入类型，再进入对应参考：

| 你看到的东西                             | 第一动作                                                             | 入口       |
| ---------------------------------- | ---------------------------------------------------------------- | -------- |
| `resources/app.asar`、Electron 安装目录 | `python scripts/asar_tool.py info app.asar`                      | electron |
| 网站 `sign`/`token`/Cookie/设备指纹      | `python scripts/js_triage.py bundle.js --out triage.md`          | js       |
| HTTP/HTTPS/WebSocket 流量、手机抓包       | `RE_CAPTURE_OUT=flows.jsonl mitmdump -s scripts/mitm_capture.py` | network  |
| 指纹浏览器/多环境/反检测                      | 检测站基线 + `browser-fingerprint.md`                                 | browser  |
| `.exe`/`.dll`/`.elf`/`.so`/加壳      | `diec sample.exe` + `env_probe.py`                               | native   |
| `.apk`/`.ipa`/Frida hook           | `jadx` / `frida-ps` + `mobile-android-ios.md`                    | mobile   |
| 想找工具/学习路线                          | `fetch_upstream.py list`                                         | awesome  |

如果目标跨域（例如 Electron 内置 JS + 抓包 + 原生模块），按“外层 → 内层”推进：桌面/App 结构 → 网络链路 → JS/字节码 → 原生 .node/.so → 算法还原。

## 4. 统一工作流（证据优先）

### E0 — 授权与隔离

记录目标、账号、范围、时间窗、允许的动作；准备隔离环境与快照；固定工具版本。运行：

```bash
python scripts/env_probe.py
python scripts/fetch_upstream.py list
```

### E1 — 静态分诊

- 文件：`file`、SHA-256、`diec`、`strings`、熵、节区/资源。
- JS：`js_triage.py`（混淆/JSVMP/WASM/加密/端点/参数/潜在密钥）。
- Electron：`asar_tool.py info/list`、fuses、`package.json`。
- 移动：`apktool`/`jadx`、manifest、so、加固特征。
- 产出：假设清单 + 下一步动态取证计划。

### E2 — 动态取证

- 网络：mitmproxy/MiteProxy/mitmproxy-mcp（证书、代理、WS）。
- 浏览器：js-reverse-mcp（断点、脚本、网络、initiator）、RuyiTrace（引擎层 trace）、Firefox-Reverse。
- 桌面：CDP `--inspect`/`--remote-debugging-port`、Frida。
- 移动：Frida hook、adb logcat、真机抓包。
- 原生：x64dbg/Ghidra + Frida/Procmon/strace。

所有结论记录 `file:line:col`、时间戳、输入/输出、工具版本、样本哈希。

### E3 — 写边界与调用链

回答：谁写入了目标字段？谁构造中间对象？谁发出请求？值来自哪里（Cookie/Storage/服务端/WASM/worker/原生）？正常与风控链路在哪里分叉？

### E4 — 还原

优先级：标准算法重写 → 自定义变换对拍 → AST 去混淆 → JSVMP/VM 黑盒/指令 trace → WASM → 补环境/纯算。Electron 的 `.jsc`/`.node` 分别走 V8 字节码边界与原生反编译。

### E5 — 验证

固定输入至少 5 条；逐字段/逐字节对比；同时验证 Cookie、Header、时间戳、随机数、TLS/HTTP2、请求顺序。签名一致不等于请求成功。

### E6 — 交付

报告 + 可执行入口 + 配置 + 验证记录 + 经验总结；事实/推断/未覆盖分开；敏感信息脱敏。

## 5. 跨域作战手册

### 5.1 Web 签名 / Token

1. 抓目标请求与触发动作（Network/mitmproxy）。
2. `js_triage.py` 找加密/签名/端点线索。
3. XHR/fetch 断点或 `get_request_initiator` 拿调用栈。
4. 断点读入参/返回值/闭包；动态字段回溯 writer。
5. 判断算法族：标准 crypto、OB、JSVMP、WASM、浏览器环境、原生。
6. 用 RuyiTrace/Firefox-Reverse 采环境证据（不可被页面 hook 干扰）。
7. Node/Python 重建，固定样本对拍。
8. 5 次真实请求验证；排查 Cookie/Header/时间戳/TLS 指纹。
9. 交付 `final.js`/`final.py`、配置、验证记录、总结。

### 5.2 Electron

1. 识别 `resources/app.asar`、fuses、版本。
2. `asar_tool.py` 解包；保留原件与哈希。
3. 读 `package.json` main → 主进程 → IPC handler → 渲染 bundle → `.node`。
4. 动态：`--inspect`（主进程）、`--remote-debugging-port`（渲染）、Frida（fuses 关闭时）。
5. `.jsc` 只做行为分析，不假设可反编译；`.node` 走 Ghidra/IDA。
6. 修改/重打包仅限授权环境，先检查完整性 fuse，输出新文件。
7. 交付证据链和可复现步骤。

### 5.3 网络协议

1. 明确是否 HTTP/1.1、HTTP/2、WebSocket、QUIC 或私有 TCP。
2. 配置代理与 CA；确认 pinning/双向 TLS。
3. 抓完整请求/响应（保存原始 bytes + hash）。
4. 找请求链：触发 → 前置 → 目标 → 后续；区分正常/风控分支。
5. 对加密 payload，转入 JS/App 侧定位加解密函数。
6. 用 Mock/重放验证字段假设；最后做真实请求验证。

### 5.4 原生二进制

1. 隔离 + 快照；`file`/哈希/`diec`/strings。
2. 静态：Ghidra/IDA；动态：x64dbg/Frida/Procmon。
3. 加壳：识别壳 → 定位 OEP → dump/修复 IAT → 再分析。
4. 打包：PyInstaller/Electron/.NET/Java 分别走对应链路。
5. 补丁只在副本上，记录偏移/preimage/rollback。
6. 交付证据、地址、复现步骤。

### 5.5 Android / iOS

1. 记录设备/系统/ABI/App 版本/签名。
2. 静态：manifest、DEX、so、资源、加固。
3. 动态：Frida hook（Java/Native）、日志、真机抓包。
4. 协议：定位加解密函数，打印输入/输出/密钥/IV；在授权环境处理 pinning。
5. 脱壳/So 修复/模拟执行按目标选择工具。
6. 还原算法并验证；重打包仅限授权 App。

### 5.6 指纹环境

1. 明确目标站与检测站；建立 baseline（IP/语言/时区/UA/视口/WebGL 等）。
2. 选内核：Chromium（VirtualBrowser/CloakBrowser/Patchright）或 Firefox（RuyiPage/Firefox-Reverse）。
3. 保持一致性：UA↔内核↔平台↔字体↔WebGL；不要每请求随机。
4. 用检测站与目标站双验证；记录“可访问”与“未被识别”的区别。
5. 自动化通过 CDP endpoint 接入（`js-reverse-mcp --browserUrl`）。
6. 遵守平台条款；不用于欺诈/未授权批量操作。

## 6. 内置脚本

| 脚本                          | 用途                                 | 示例                                                                   |
| --------------------------- | ---------------------------------- | -------------------------------------------------------------------- |
| `scripts/env_probe.py`      | 工具链探测 + 安装提示                       | `python scripts/env_probe.py --category binary`                      |
| `scripts/asar_tool.py`      | 纯 Python ASAR 列表/提取/校验             | `python scripts/asar_tool.py extract app.asar out/ --verify`         |
| `scripts/js_triage.py`      | JS 混淆/加密/端点分诊                      | `python scripts/js_triage.py bundle.js --out triage.md`              |
| `scripts/hook_gen.py`       | 生成 fetch/xhr/WS/cookie/crypto/hook | `python scripts/hook_gen.py --type all --out hooks.js`               |
| `scripts/mitm_capture.py`   | mitmproxy JSONL 取证 addon           | `RE_CAPTURE_OUT=flows.jsonl mitmdump -s scripts/mitm_capture.py`     |
| `scripts/fetch_upstream.py` | 浏览/检查/浅克隆 41 个上游                   | `python scripts/fetch_upstream.py fetch js-reverse-mcp --dest tools` |

脚本都是标准库优先；Frida/mitmproxy/Ghidra 等外部工具按需安装。运行前先读脚本头部注释。

## 7. 上游工具目录（不丢能力的关键）

`assets/upstream-catalog.json` 记录了 md.md 中全部 41 个来源：URL、分类、能力、安装方式、对应参考、状态。`fetch_upstream.py` 可直接按需克隆，保留上游完整能力，而不是把第三方代码硬塞进本技能。

```bash
python scripts/fetch_upstream.py list --category js
python scripts/fetch_upstream.py check --limit 5
python scripts/fetch_upstream.py fetch --category network --dest ./upstream
```

说明：

- 原 `LoseNine/Firefox-FingerPrint-Analyzer` 已 404；其能力与文档由 `erma0/js-reverse-skill`（RuyiTrace 集成）保留，详见 `references/js-web-reverse.md` 与 `source-coverage.md`。
- skills.rest 的 `re-electron` 镜像源为 `dslsdzc/rev-skills`。
- `Exe-Decompiler` 为闭源商业工具，本技能提供开源等价链路。
- `PE-reverse-skill` 中的 LLM jailbreak 组件不属于本技能范围，已排除；仅保留合法逆向能力。
- 各上游许可证不同；本技能只做引用/编排，不重新分发其代码。

## 8. 证据与报告规范

每次任务建立：

```
case/
├── original/          # 原始样本/抓包（只读）
├── hashes.txt         # SHA-256
├── notes/
│   ├── timeline.md
│   ├── hypotheses.md  # 事实/推断分开
│   └── requests.md    # 请求链
├── evidence/          # 断点、日志、截图、导出
└── result/            # 交付物
```

报告骨架：

1. 目标与授权
2. 环境与工具版本
3. 样本/流量与哈希
4. 静态证据
5. 动态证据（调用栈、输入/输出、时间）
6. 算法/协议还原
7. 复现实现与验证记录
8. 限制、未覆盖、风险
9. 附件清单

硬规则：

- 不把推断写成事实；没有证据就标注“未覆盖”。
- 不把截断日志当成真实值（尤其 RuyiTrace ~4000 字符）。
- 不泄露密钥/凭据；截图打码。
- 不交付“只在浏览器里能跑”的实现，除非明确选择浏览器交付并说明。
- 不用未验证的 AI 生成值填充 fixture。

## 9. 参考索引

- `references/electron-desktop.md` — ASAR、re-electron、CDP、Frida、fuses、.jsc、MiniMax 案例
- `references/js-web-reverse.md` — 证据模型、js-reverse-mcp、jshook、hello、reverse-skill、deobfuscator、evolver、Firefox-Reverse、RuyiTrace、REOT、去混淆手册
- `references/network-capture.md` — mitmproxy、MiteProxy、mitmproxy-mcp、证书、WS、真机
- `references/browser-fingerprint.md` — 指纹面、VirtualBrowser、Luna、Firefox/Ruyi、资源地图、TideFinger
- `references/native-binary.md` — Ghidra、DIE、x64dbg、PE Reverse Analyzer、PyInstaller、VMP、工具索引
- `references/mobile-android-ios.md` — Android 工具链、Frida/RxApp、脱壳、iOS、抓包
- `references/awesome-learning.md` — 六份 awesome 列表、工具短名单、12 周路径
- `references/source-coverage.md` — 41 个来源逐项覆盖与能力去向
