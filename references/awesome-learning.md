# 资源、学习路径与工具索引

覆盖来源：`AlienwareHe/awesome-reverse`、`morluto/awesome-reverse-engineering`、`edwardtay/awesome-reverse-engineering`、`tylerha97/awesome-reversing`、`ReversingID/Awesome-Reversing`、`6700github/awesome-reverse-engineering`。另交叉引用 `lmy375/awesome-vmp`、`WuFengXue/android-reverse`、`zhaotoday/fingerprint-browser`、`weixinbao/ReverseTool`。

> 这些是导航型资源，不是一份“照着做就能入侵”的教程。所有技术只用于授权测试、CTF、恶意软件防御分析、互操作研究和个人学习。

## 1. 六份 Awesome 列表的定位

| 仓库                                     | 语言  | 强项                                                                                      | 适合           |
| -------------------------------------- | --- | --------------------------------------------------------------------------------------- | ------------ |
| AlienwareHe/awesome-reverse            | 中文  | JS（PC/H5/WebView/小程序）、Android（Xposed/Frida/脱壳/So）、学习路径                                  | 中文入门到进阶      |
| morluto/awesome-reverse-engineering    | 英文  | 现代分类：triage、native、debuggers、instrumentation、malware、mobile、firmware、formats、diffing、AI | 建立全景图        |
| edwardtay/awesome-reverse-engineering  | 英文  | 130+ 工具、安全标签、维护数据、MCP、12 周路径、recipes、智能合约                                               | Agent 时代工具选型 |
| tylerha97/awesome-reversing            | 英文  | 书籍/课程/频道/练习、Hex/反汇编/动态分析/Android/Yara                                                   | 初学者系统学习      |
| ReversingID/Awesome-Reversing          | 英文  | 按软件/硬件/格式/数据库四域拆分                                                                       | 扩展逆向视野       |
| 6700github/awesome-reverse-engineering | 中文  | 超大型 IDA/Ghidra/x64dbg/Frida/Unicorn 插件与文章索引                                             | 查冷门插件/脚本     |

## 2. AlienwareHe/awesome-reverse（中文学习路径）

仓库地址：https://github.com/AlienwareHe/awesome-reverse

目录主题：

- 工具环境
- JS 逆向（PC/H5）
  - 未混淆 JS 调试与算法还原
  - Node 环境模拟执行 JS
  - 浏览器环境补齐
  - JDK 中 V8/Nashorn 引擎使用
  - OB 混淆 AST 还原
  - Android WebView Hook、JS Bridge 注入
  - 微信小程序架构、反编译与代码修复、渲染/逻辑层 Hook、网络请求 Hook
- Android 入门
  - 基础知识、Xposed Hook、Xposed 原理、关键代码定位
  - 重打包与签名校验绕过
  - 设备指纹模拟、Native Hook、自动点击、Hook RPC
  - 全协议还原、TCP 请求抓包
- Android 进阶
  - ELF 格式、Frida、加固/脱壳、ARM 指令/调用约定
  - Riru/EdXp、JNI 静动态注册、Ratel
- 视频课程/公众号/交流群

用法：先按“JS 或 Android”选主线，再搭配本技能的 `js-web-reverse.md` / `mobile-android-ios.md` 实操。

## 3. morluto/awesome-reverse-engineering（现代全景）

仓库地址：https://github.com/morluto/awesome-reverse-engineering

章节：

- Start here / Contents
- Learning / Books
- File identification and triage
- Native analysis
- Debuggers
- Dynamic instrumentation and tracing
- Malware analysis
- Android and managed code
- iOS and macOS
- Language runtimes and packagers
- Web and protocols
- Firmware and hardware
- File formats
- Diffing and analysis frameworks
- AI-assisted analysis
- Practice and communities
- Related lists

代表性工具（按章节）：IDA/Ghidra/Binary Ninja、x64dbg/LLDB/WinDbg、Frida/DTrace/eBPF、YARA、radare2/rizin、angr、Triton、Qiling、Unicorn、Frida、Objection、jadx/apktool、dnSpy/ILSpy、binwalk、ImHex/Kaitai、Diaphora/BinDiff、MCP/LLM-assisted RE。

适用：不想被单一平台/语言限制时，用它的分类建立自己的工具矩阵。

## 4. edwardtay/awesome-reverse-engineering（工具选型 + 安全标签）

仓库地址：https://github.com/edwardtay/awesome-reverse-engineering

特点：

- 130+ 工具，每条带安全/维护标签（便于避开停止维护/高风险项目）。
- 按运行时 triage：Native、.NET、Java/Android、JS/Web、Firmware、Smart Contracts。
- 包含 MCP servers / AI-assisted RE 章节（与本技能相关）。
- 12 周学习路径；recipes（常见任务组合）；练习靶场。
- 安全第一：隔离实验室、授权、样本处理。

推荐用法：

1. 按目标运行时选章节（如 `.NET` 或 `Firmware`）。
2. 看安全标签和维护状态，优先活跃项目。
3. 参考 recipes 组合工具，而不是逐个试。

## 5. tylerha97/awesome-reversing（经典入门）

仓库地址：https://github.com/tylerha97/awesome-reversing

章节：Books、Courses、Channels、Practice、Hex Editors、Binary Format、Disassemblers/Decompilers、Binary Analysis、Bytecode Analysis、Import Reconstruction、Dynamic Analysis、Debugging、Mac Decrypt、Document Analysis、Scripting、Android、Yara。

适合：从零建立词汇表；配合实践靶场（crackmes.one、pwn.college、Root-Me、Hack The Box 等）练习。

## 6. ReversingID/Awesome-Reversing（四域拆分）

仓库地址：https://github.com/ReversingID/Awesome-Reversing

四个域，每个有独立文件：

- Software：可执行文件、字节码、库；IDA/Ghidra/Binary Ninja/x64dbg/Frida/angr；CTF、恶意软件、漏洞研究、DRM、游戏 mod。
- Hardware：PCB、芯片、嵌入式固件；逻辑分析仪、示波器、JTAG/SWD、OpenOCD、binwalk；IoT、固件提取、协议逆向、芯片开盖。
- Format：文件格式/网络协议/游戏资源；010 Editor、HexFiend、Kaitai Struct、ImHex、Wireshark；资源提取、协议文档、互操作。
- Database：SQLite/MDB/关系/NoSQL；schema 恢复、数据考古、迁移。

价值：当目标不是“一个 exe”而是固件、协议或数据格式时，从这里进入。

## 7. 6700github/awesome-reverse-engineering（插件/文章巨型索引）

仓库地址：https://github.com/6700github/awesome-reverse-engineering

特点：体量极大（README 数百 KB），以 IDA 插件/脚本为主，另有 Ghidra、x64dbg、Frida、Unicorn 等章节。

IDA 章节分类：

- 插件与脚本（新添加/未分类）
- 结构体/类检测、创建、恢复
- 外观/主题
- 固件/嵌入式
- 签名（FLIRT）/比较/Diff/匹配
- IDB 操作、协作逆向
- 与调试器同步/通信
- 导入导出/与其他工具交互
- 特定分析目标
- IDAPython、指令参考、辅助脚本
- 调试/动态运行/动态数据
- 反编译器/AST、反混淆
- 效率/导航/可视化
- Android/Apple/ELF/Microcode
- 模拟器集成、漏洞、补丁、函数、污点/符号执行、字符串、加密解密
- 文章：Tips、系列教程、工具介绍、翻译、实战、IDA 对抗

用法：先按目标平台/任务定位章节，再回到本技能对应领域参考；不要在未验证的情况下批量安装旧插件（兼容性/安全风险）。

## 8. 按任务的工具短名单

| 任务           | 工具                                                                       |
| ------------ | ------------------------------------------------------------------------ |
| 文件类型/壳       | DIE、ExifTool、binwalk、strings                                             |
| 反汇编/反编译      | Ghidra、IDA、Binary Ninja、radare2/rizin、Cutter                             |
| Windows 调试   | x64dbg、WinDbg、Process Monitor、API Monitor                                |
| 动态插桩         | Frida、DynamoRIO、Pin、Intel PT                                             |
| 模拟/符号执行      | Unicorn、Qiling、angr、Triton、unicorn                                       |
| .NET         | dnSpy、ILSpy、de4dot、dotPeek                                               |
| Java/Android | jadx、apktool、JEB、GDA、dex2jar、Frida                                       |
| iOS          | IDA、Hopper、class-dump、Cycript、LLDB、Theos、Frida                           |
| JS/Web       | Chrome DevTools、js-reverse-mcp、js-deobfuscator、RuyiTrace、Firefox-Reverse |
| 网络           | mitmproxy、MiteProxy、Wireshark/tshark、Charles                             |
| 指纹浏览器        | VirtualBrowser、Camoufox、CloakBrowser、Patchright、Luna                     |
| 固件           | binwalk、firmware-mod-kit、Ghidra、JTAG/SWD                                 |
| 恶意软件         | YARA、CAPA、FLOSS、PE-sieve、Volatility                                      |
| 二进制 diff     | Diaphora、BinDiff、radiff2                                                 |

## 9. 12 周学习路径（参考 edwardtay/tylerha97）

1. 基础：计算机体系结构、汇编、ELF/PE、C/C++、Python。
2. 静态：反汇编器使用、函数识别、字符串/导入、调用约定。
3. 动态：调试器、断点、内存、调用栈、strace/Procmon。
4. 插桩：Frida、Hook、trace、脚本。
5. 保护：加壳、混淆、反调试、VMProtect 概念。
6. Web/JS：DevTools、请求链、AST、JSVMP、WASM。
7. 移动：APK 结构、jadx、Frida、抓包、native。
8. 固件/协议：binwalk、UART/JTAG、Wireshark、Kaitai。
9. 实战：CTF crackme、恶意样本、漏洞研究、报告写作。
10. 工程化：自动化、证据管理、可复现、合规。

## 10. 练习与社区

- CTF/靶场：crackmes.one、pwn.college、Root-Me、Hack The Box、TryHackMe、picoCTF。
- 社区：看雪、52pojie、Reddit r/ReverseEngineering、RE Discord、Tuts4You、EXETools。
- 会议/论文：Black Hat、DEF CON、REcon、HITB、USENIX；awesome-vmp 的会议 PPT/论文章节。
- 书籍：Practical Reverse Engineering、The IDA Pro Book、Reverse Engineering for Beginners、Malware Analyst's Cookbook 等（见 tylerha97 书籍章节）。

# 
