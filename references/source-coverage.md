# 来源覆盖矩阵（41/41）

本文件证明 `C:\Users\juang\Desktop\md.md` 中的每一个来源都已进入统一技能，并给出去向。机器可读版本见 `assets/upstream-catalog.json`（41 条，id 唯一）。

状态说明：

- **完整**：能力、命令/用法与工作流产出于对应参考。
- **保留（替代）**：原仓库不可用，但其能力由同源/后继项目与文档保留。
- **能力映射**：闭源/商业工具，用开源等价链路实现同等能力。
- **资源**：导航型列表，保留分类、关键条目与链接。
- **排除**：明确不属于本技能范围（如 LLM jailbreak），在表中注明并说明保留的合法部分。

| # | 来源 | 类型/状态 | 保留的能力 | 覆盖位置 |
| ---: | --- | --- | --- | --- |
| 1 | [cuddlesgiggles/minimax-design-auth](https://github.com/cuddlesgiggles/minimax-design-auth) | 案例/完整 | Hilo 桌面登录态路径、AES-256-GCM token envelope、`.token-key`、JWT、模型/积分 API | `electron-desktop.md` §8 |
| 2 | [electron/asar](https://github.com/electron/asar) | 工具/完整 | pack/list/extract/extract-file、格式、去重、完整性、程序化 API；纯 Python 等价工具 | `electron-desktop.md` §2；`scripts/asar_tool.py` |
| 3 | [jonmest/How-To-Tamper-With-Any-Electron-Application](https://github.com/jonmest/How-To-Tamper-With-Any-Electron-Application) | 指南/完整 | ASAR 解包→修改→重打包、完整性/签名注意事项 | `electron-desktop.md` §3 |
| 4 | [parsiya/evil-electron](https://github.com/parsiya/evil-electron) | 工具/完整 | preload 注入、app.asar 替换、asar pack、权限边界 | `electron-desktop.md` §3 |
| 5 | [fmartini23/electron-dev-tools](https://github.com/fmartini23/electron-dev-tools) | 工具/完整 | 统一 console、IPC 监控、主/渲染进程日志 | `electron-desktop.md` §6 |
| 6 | [frida/frida](https://github.com/frida/frida) | 框架/完整 | spawn/attach、函数 hook、native hook、跨桌面/移动 | `electron-desktop.md` §5；`mobile-android-ios.md` §3 |
| 7 | [skills.rest re-electron](https://skills.rest/skill/re-electron-dslsdzc) | 技能/完整 | ASAR、CDP 主/渲染、V8 `.jsc`、fuses、反调试、`.node`；源仓库 `dslsdzc/rev-skills` | `electron-desktop.md` §4；catalog `re-electron-skill` |
| 8 | [mitmproxy/mitmproxy](https://github.com/mitmproxy/mitmproxy) | 框架/完整 | HTTP/1.1、HTTP/2、WebSocket、TUI/Web/CLI、addon、TLS 拦截 | `network-capture.md` §2；`scripts/mitm_capture.py` |
| 9 | [yakrsa/MiteProxy](https://github.com/yakrsa/MiteProxy) | 工具/完整 | 类 Fiddler GUI、自动系统代理、Mock、JSONPath、重放/对比、WS、HAR、弱网、会话 | `network-capture.md` §3 |
| 10 | [Aillumine/mitmproxy-mcp](https://github.com/Aillumine/mitmproxy-mcp) | MCP/完整 | MCP 抓包、搜索/分片读取、Mock、Android adb reverse、iOS、Web UI、证书 | `network-capture.md` §4 |
| 11 | [kuizuo/js-deobfuscator](https://github.com/kuizuo/js-deobfuscator) | 工具/完整 | Babel AST 去混淆、decoder 发现、字符串数组、CFF、反自保护、CLI/API/Playground | `js-web-reverse.md` §8 |
| 12 | [zhizhuodemao/js-reverse-mcp](https://github.com/zhizhuodemao/js-reverse-mcp) | MCP/完整 | 24 工具：脚本/断点/单步/网络/WS/initiator/Cookie 重放/Patchright/CloakBrowser | `js-web-reverse.md` §4 |
| 13 | [wuji66dde/jshook-skill](https://github.com/wuji66dde/jshook-skill) | 技能/完整 | 收集/搜索/AI 反混淆/加密检测/CDP 调试/断点/Hook/stealth/DOM/页面控制 | `js-web-reverse.md` §5 |
| 14 | [erma0/js-reverse-skill](https://github.com/erma0/js-reverse-skill) | 技能/完整 | ruyipage+RuyiTrace 证据门禁、黑盒补环境/纯算、59 案例、Node/Python 交付、AST/验证码/WASM 工具 | `js-web-reverse.md` §2、§11 |
| 15 | [WhiteNightShadow/hello_js_reverse_skill](https://github.com/WhiteNightShadow/hello_js_reverse_skill) | 技能/完整 | 双语言还原、JSVMP/WASM、动态 Cookie、Camoufox MCP、脚本/模板/案例 | `js-web-reverse.md` §6 |
| 16 | [WhiteNightShadow/firefox-reverse](https://github.com/WhiteNightShadow/firefox-reverse) | 桌面/完整 | 内置 AI Agent、71 工具、引擎级 trace、指纹环境、director MCP、两阶段路线 | `js-web-reverse.md` §10 |
| 17 | [LoseNine/Firefox-FingerPrint-Analyzer](https://github.com/LoseNine/Firefox-FingerPrint-Analyzer) | 已删除/**保留（替代）** | RuyiTrace 引擎层 NDJSON、jscall/opcode/JSVMP/WASM/WS、TRACE_GATE、eval 源码、指纹基线；文档/脚本由 `erma0/js-reverse-skill` 保留 | `js-web-reverse.md` §11；catalog `ruyitrace` |
| 18 | [Evil0ctal/Reverse-Engineering-Online-Toolkit](https://github.com/Evil0ctal/Reverse-Engineering-Online-Toolkit) | 工具/完整 | 100+ 在线工具：编码/压缩/哈希/KDF/对称/非对称/协议/二进制/XOR/cURL/生成器 | `js-web-reverse.md` §12 |
| 19 | [715494637/reverse-skill](https://github.com/715494637/reverse-skill) | 技能/完整 | 请求链证据、写边界、JSVMP/AST/worker/WASM/webpack 恢复、运行时对齐、检查点、交接文档 | `js-web-reverse.md` §7 |
| 20 | [JiangtaoQu/js-reverse-evolver](https://github.com/JiangtaoQu/js-reverse-evolver) | MCP/完整 | `evolve_js`、知识查询/注入、状态、MemOS/GitNexus/Stagehand、自学习模式晋升 | `js-web-reverse.md` §9 |
| 21 | [Virtual-Browser/VirtualBrowser](https://github.com/Virtual-Browser/VirtualBrowser) | 桌面/完整 | 多环境隔离、UA/代理/语言/时区/WebRTC/Canvas/WebGL/Audio、Playwright | `browser-fingerprint.md` §2 |
| 22 | [musiclover789/luna](https://github.com/musiclover789/luna) | 框架/完整 | Go 自动化、抗指纹浏览器、CDP、指纹项、拟人动作、代理 | `browser-fingerprint.md` §3 |
| 23 | [zhaotoday/fingerprint-browser](https://github.com/zhaotoday/fingerprint-browser) | 资源/完整 | 27 款商业浏览器、28 家代理、开源浏览器/内核/框架/生成库/检测站/教程 | `browser-fingerprint.md` §5 |
| 24 | [hisune/antidetect-browser](https://github.com/hisune/antidetect-browser) | 资源/完整 | 商业指纹浏览器对比、免费环境、检测站 | `browser-fingerprint.md` §6 |
| 25 | [NationalSecurityAgency/ghidra](https://github.com/NationalSecurityAgency/ghidra) | 框架/完整 | 反汇编/反编译/图谱/脚本/headless/多架构/扩展 | `native-binary.md` §3 |
| 26 | [horsicq/Detect-It-Easy](https://github.com/horsicq/Detect-It-Easy) | 工具/完整 | 文件类型、壳/保护器、启发式、DiE-JS、diec、支持格式 | `native-binary.md` §2 |
| 27 | [x64dbg/x64dbg](https://github.com/x64dbg/x64dbg) | 工具/完整 | Windows 用户态调试、x86/x64、插件、Scylla、脚本、补丁 | `native-binary.md` §4 |
| 28 | [lmy375/awesome-vmp](https://github.com/lmy375/awesome-vmp) | 资源/完整 | VMP/CV 工具（FKVMP、VMP 插件、VMSweeper、Oreans、VMAttack、VirtualDeobfuscator）+ 文章/论文 | `native-binary.md` §8 |
| 29 | [itsKayWat/Exe-Decompiler](https://github.com/itsKayWat/Exe-Decompiler) | 商业/**能力映射** | 二进制分类、ASAR、PyInstaller、PE 资源、source map、GUI → 开源等价链路 | `native-binary.md` §7 |
| 30 | [MrWQ/reverse_pyinstaller](https://github.com/MrWQ/reverse_pyinstaller) | 工具/完整 | PyInstaller 提取、pyc 头修复、`--key` 解密、批量输出 | `native-binary.md` §6 |
| 31 | [weixinbao/ReverseTool](https://github.com/weixinbao/ReverseTool) | 资源/完整 | Java/Android/C++/.NET/iOS 工具索引与 Hook 框架 | `native-binary.md` §9；`mobile-android-ios.md` §7 |
| 32 | [DamonZS/PE-reverse-skill](https://github.com/DamonZS/PE-reverse-skill) | 技能/完整（合法部分） | PE 分析、Ghidra/Frida、内存/注入、patch/rollback、Android、协议、源码骨架、Dashboard；**LLM jailbreak 组件排除** | `native-binary.md` §5；`mobile-android-ios.md` §6 |
| 33 | [langgithub/RxAppEncryptionProtocol](https://github.com/langgithub/RxAppEncryptionProtocol) | 工具/完整 | Frida Hook MD5/AES/DES/RSA、SSL pinning、native 动态注册、协议还原 | `mobile-android-ios.md` §3.1 |
| 34 | [WuFengXue/android-reverse](https://github.com/WuFengXue/android-reverse) | 资源/完整 | 脱壳、so/native、GUI/CLI 反编译、Hook 框架、工具对比 | `mobile-android-ios.md` §1 |
| 35 | [AlienwareHe/awesome-reverse](https://github.com/AlienwareHe/awesome-reverse) | 资源/完整 | 中文 JS/Android/Native 学习路径、WebView/小程序、Xposed/Frida、ELF/ARM、脱壳 | `awesome-learning.md` §2 |
| 36 | [morluto/awesome-reverse-engineering](https://github.com/morluto/awesome-reverse-engineering) | 资源/完整 | 现代分类：triage/native/debug/instrumentation/malware/mobile/firmware/format/diff/AI | `awesome-learning.md` §3 |
| 37 | [edwardtay/awesome-reverse-engineering](https://github.com/edwardtay/awesome-reverse-engineering) | 资源/完整 | 130+ 工具、安全标签、维护数据、MCP、12 周路径、recipes、智能合约 | `awesome-learning.md` §4 |
| 38 | [tylerha97/awesome-reversing](https://github.com/tylerha97/awesome-reversing) | 资源/完整 | 书籍/课程/频道/练习、Hex/反汇编/动态/Android/Yara | `awesome-learning.md` §5 |
| 39 | [ReversingID/Awesome-Reversing](https://github.com/ReversingID/Awesome-Reversing) | 资源/完整 | 软件/硬件/格式/数据库四域分类与工具 | `awesome-learning.md` §6 |
| 40 | [6700github/awesome-reverse-engineering](https://github.com/6700github/awesome-reverse-engineering) | 资源/完整 | 巨型 IDA/Ghidra/x64dbg/Frida/Unicorn 插件与文章索引、分类导航 | `awesome-learning.md` §7 |
| 41 | [TideSec/TideFinger_Go](https://github.com/TideSec/TideFinger_Go) | 工具/完整 | Web/主机指纹识别、2.3 万+ 指纹、URL/IP/CIDR、POC 详情、并发、CMS 标注 | `browser-fingerprint.md` §7 |

## 验证

```bash
python -c "import json; d=json.load(open('assets/upstream-catalog.json',encoding='utf-8')); print(len(d['sources']))"
# 41
python scripts/fetch_upstream.py list
python scripts/fetch_upstream.py check --limit 5
```

- 41 个来源全部有 catalog 条目；每条有 `ref` 指向覆盖文档。
- 原仓库 404 的 RuyiTrace 用同源 `erma0/js-reverse-skill` 的文档与脚本保留，并在 catalog 标注 `deleted-upstream` 与 `alternative`。
- skills.rest 镜像指向真实源仓库，避免只依赖展示页。
- `PE-reverse-skill` 的 LLM jailbreak/跨平台指令注入组件被明确排除；这是唯一的能力排除，属于安全边界，不是遗漏。
- 第三方许可证各不相同：本技能只编排/引用，不重新分发上游代码；商业/闭源工具标注为映射或需自行获取。
- 如上游未来变更/删除，`fetch_upstream.py check` 会报告；参考文档仍保留能力说明与替代路径。
