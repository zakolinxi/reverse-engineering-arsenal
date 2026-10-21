# 原生二进制 / PE / 加壳与打包

覆盖来源：`NationalSecurityAgency/ghidra`、`horsicq/Detect-It-Easy`、`x64dbg/x64dbg`、`lmy375/awesome-vmp`、`itsKayWat/Exe-Decompiler`、`MrWQ/reverse_pyinstaller`、`weixinbao/ReverseTool`、`DamonZS/PE-reverse-skill`

## 1. 首轮分诊（10 分钟）

```bash
sha256sum sample.exe
file sample.exe
strings -n 6 sample.exe | head -100
diec sample.exe                 # Detect It Easy CLI
# 或 GUI：die sample.exe
```

记录：文件类型、架构、位数、编译器、打包器/保护壳、导入表异常、节区熵、签名、overlay、资源。`python scripts/env_probe.py` 可确认 DIE/Ghidra/x64dbg 等是否就绪。

判断线索：

- 节区名 `UPX0/UPX1`、高熵、异常入口点 → 可能压缩/加壳。
- `.vmp`/`.themida`/`.enigma` 等节区或 DIE 标记 → VMProtect/Themida/Enigma 等。
- `.NET`/`mscoree` → .NET，用 dnSpy/ILSpy/de4dot。
- Java/JAR → jd-gui/Luyten/CFR/Procyon。
- PyInstaller → `PYZ-00.pyz`、`pyi-*`、Python DLL。
- Electron → `resources/app.asar`（见 `electron-desktop.md`）。
- Go → Go build ID/panic strings；Rust → 大量符号/`rustc` 字符串。

## 2. Detect It Easy（DIE）

三种形态：

- `die`：图形界面，适合探索签名/规则。
- `diec`：命令行，适合批量分诊。
- `diel`：轻量 GUI（仅扫描）。

支持：PE、ELF、APK、IPA、JAR、ZIP、ISO9660、DEX、MS-DOS、COM、LE/LX、Mach-O、NPM、Amiga、通用 Binary。

安装：Windows `choco install die` / Microsoft Store；Linux 发行版包 / AUR / OBS；Docker 构建。使用 `diec --help` 查看当前版本的批量/JSON 参数。

DIE 的价值在于“文件类型 + 打包器/保护器 + 编译器 + 启发式证据”，不要把它当杀毒结论；启发式结果会单独展示证据，需要人工判断。

## 3. Ghidra

安装：

1. 安装 **JDK 25 64-bit**。
2. 下载官方多平台 release（`ghidra_<version>_<release>_<date>.zip`，不是 Source Code）。
3. 解压到新目录，运行 `ghidraRun`（Windows `ghidraRun.bat`）或 `support/pyghidraRun`。

GUI 工作流：

1. New Project → Import File（自动识别格式/架构）。
2. Analyze（默认分析器；必要时调整编译器/基址）。
3. 从入口点/导入/导出/字符串交叉引用开始；重命名函数/变量；使用 Decompiler。
4. 对 C++：恢复 RTTI/虚表、STL 容器、调用约定；对 Go/Rust：利用符号/字符串。
5. 保存项目、导出反编译 C、记录地址与哈希。

Headless（自动化/批量）：

```bash
# Linux/macOS
support/analyzeHeadless <project_dir> <project_name> -import sample.exe -overwrite \
  -scriptPath <scripts> -postScript MyExport.java

# Windows
support\analyzeHeadless.bat C:\ghidra-projects REA -import C:\samples\sample.exe -overwrite ^
  -scriptPath C:\scripts -postScript ExportDecomp.java
```

常用参数：`-processor`、`-loader`、`-analysisTimeoutPerFile`、`-deleteProject`、`-preScript`。无头模式适合生成函数列表/反编译文本/导入导出清单，再由人复核。

Ghidra 扩展：可用 Java/Python（PyGhidra）脚本；常用能力包括函数签名、结构体恢复、调用图、符号执行/污点（插件）、WASM/固件加载。旧版本有已知安全漏洞，先看 Security Advisories。

## 4. x64dbg

安装：下载 snapshot，解压到可写目录；`x96dbg.exe` 注册 shell 扩展/快捷方式；32 位用 `x32\x32dbg.exe`，64 位用 `x64\x64dbg.exe`。

工作流：

1. File → Open 目标；EntryBreakpoint/系统断点。
2. 查看 CPU、内存映射、模块、线程、句柄、调用栈。
3. 字符串/导入/导出/符号搜索；在关键 API 下断点（`CreateFileW`、`InternetOpenUrlW`、`CryptDecrypt` 等）。
4. 条件断点/日志断点（命令栏）；追踪寄存器/内存；执行到返回。
5. 识别 packer 后：在 OEP 附近下硬件断点/内存断点，dump 进程（Scylla 修复 IAT）。
6. Patch：修改指令/内存；保存到新文件（不要覆盖原件）。
7. 插件：Scylla、xAnalyzer、OllyDumpEx 等；脚本用 x64dbg 命令/插件。

常用命令（命令栏）：`bp <addr>`、`bc`、`bpcond <addr>,<cond>`、`run`、`step`、`dump <addr>`、`memmap`、`modcall`、`savedata`、`patch`。具体语法以当前版本 `help` 为准。

反调试/反 VM 只作为分析障碍处理：识别检测点、记录证据；在你的授权环境中可 patch 或 hook 跳过。不要把绕过技术用于规避第三方软件保护。

## 5. PE Reverse Analyzer（DamonZS/PE-reverse-skill）

安装：

```bash
git clone https://github.com/DamonZS/PE-reverse-skill
python -m pip install -r requirements.txt   # pefile, capstone, requests
python -m reverse_analyzer --help
python -m reverse_analyzer list-tools
```

能力与命令（节选）：

```bash
# 环境/能力
python -m reverse_analyzer environment validate --out .\out
python -m reverse_analyzer environment validate --execute-probes --out .\out
python -m reverse_analyzer capability list

# 静态 + 可选 Ghidra/Frida/GUI
python -m reverse_analyzer analyze .\sample.exe --out .\out --max-iterations 3
python -m reverse_analyzer analyze .\sample.exe --out .\out --decompile --ghidra-home C:\ghidra
python -m reverse_analyzer analyze .\sample.exe --out .\out --dynamic --dynamic-backend frida --dynamic-profile auto
python -m reverse_analyzer analyze .\sample.exe --out .\out --gui --gui-runtime --gui-visual --reconstruct-gui

# 运行时内存（Windows，真实副作用，务必在 VM）
python -m reverse_analyzer memory scan --pid 4242 --out .\memory-scan --pattern "4D 5A" --pattern-type aob
python -m reverse_analyzer memory read --pid 4242 --out .\memory-read --address 0x7FF600001000 --size 256

# PE patch：plan → verify → apply → rollback（输入只读，输出新文件）
python -m reverse_analyzer patch plan .\sample.exe --out .\patch-session --strategy inline_patch --offset 0x120 --replacement "90 90" --operation-id replace-branch
python -m reverse_analyzer patch verify .\sample.exe --plan .\patch-session\patch\plan.json --out .\patch-session\patch
python -m reverse_analyzer patch apply .\sample.exe --plan .\patch-session\patch\plan.json --out .\patched.exe --artifact-dir .\patch-session\patch
python -m reverse_analyzer patch rollback .\patched.exe --plan .\patch-session\patch\rollback_plan.json --out .\restored.exe --artifact-dir .\patch-session\patch

# 协议证据（被动文件，不是实时抓包）
python -m reverse_analyzer protocol capture .\traffic.pcapng --out .\protocol-out --format auto
python -m reverse_analyzer protocol infer .\messages.jsonl --out .\protocol-infer --format jsonl
python -m reverse_analyzer protocol summarize .\stream.bin --out .\protocol-summary --format raw

# 源码骨架（保守，不等于完整源码恢复）
python -m reverse_analyzer source reconstruct .\sample.exe --out .\source-out --strategy auto --decompile --gui

# Dashboard
python -m reverse_analyzer dashboard --workspace . --out .\dashboard --serve --host 127.0.0.1 --port 8088
```

状态语义：`unavailable`（平台/依赖不满足，副作用前停止）、`partial`（有结果但深度解析器/依赖缺失）、`failed`（真实失败，不伪装成可用）。

边界：

- `memory write` 要求 `--expected` 且等长替换；`protect` 范围必须在一个 committed region；`free` 只接受精确 allocation base。
- `patch` 当前可靠路径是等长 `inline_patch`；高级策略需要当前 CLI 未暴露的字段，不要假设可用。
- 缺 `pefile` 时 patch 返回 `unavailable`；缺 Capstone/非 x86/x64 时验证失败。
- 只读分析不需要副作用；内存/注入/hook 必须显式授权并优先 `--rollback`。
- 该仓库还包含 LLM jailbreak/指令注入组件；**本技能不采用、不复制**，只保留合法的逆向分析能力。

## 6. PyInstaller 逆向

### 6.1 标准路径

```bash
python pyinstxtractor.py target.exe
# 生成 target.exe_extracted/
```

- 提取主程序 pyc、`PYZ-00.pyz`、依赖 DLL、资源。
- PyInstaller 会剥离 pyc 的 8 字节头（magic + timestamp）。从 `struct` 或同版本 Python 的 magic 补回，或使用维护中的 pyinstxtractor 版本自动处理。
- `.pyc` 反编译：`decompyle3`/`uncompyle6`（旧版本）、`pycdc`（Decompyle++）、或匹配版本的 `uncompyle6`。Python 3.12+ 的 pyc 支持有限，优先找源码/字节码语义分析。
- PyInstaller 6+ 自带 `pyi-archive_viewer` 可列/提取归档。
- 加密 `--key` 的 PyInstaller：需要找到 key（`pyimod00_crypto_key`/运行时）并解密；`MrWQ/reverse_pyinstaller` 支持该路径。

### 6.2 MrWQ/reverse_pyinstaller

```bash
git clone https://github.com/MrWQ/reverse_pyinstaller
cd reverse_pyinstaller
python reverse_pyexe.py C:\path\target.exe
# 默认输出到 target.exe_out
```

流程：pyinstxtractor 提取 → 修复 pyc 头（`struct`/`hextool.py`）→ 批量输出 pyc → 用同版本反编译器还原。匹配 Python 版本非常重要；Python 3.8 时代工具对 3.11+ 可能不适用。只在你拥有的软件上使用。

## 7. Exe-Decompiler（商业工具映射）

`itsKayWat/Exe-Decompiler` 是闭源 SaaS/GUI（Windows），提供二进制分类、ASAR、PyInstaller、PE 资源、source map、结果浏览。它不提供可审计的开源实现；用以下等价链路替代：

| 需求            | 开源链路                                      |
| ------------- | ----------------------------------------- |
| Electron/ASAR | `scripts/asar_tool.py` / `@electron/asar` |
| PyInstaller   | `pyinstxtractor` / `reverse_pyexe.py`     |
| PE 头/资源       | `pefile`、DIE、Ghidra、x64dbg                |
| 文件分类          | DIE `diec`                                |
| Source map    | DevTools / `source-map`                   |
| GUI           | Ghidra、Cutter/rizin、x64dbg                |

## 8. VMProtect / 虚拟化保护（awesome-vmp）

`lmy375/awesome-vmp` 汇总了 VMProtect/Code Virtualizer/Oreans 系列的分析工具与文章。典型工具：

| 工具                   | 目标                                      | 形态             | 说明                                 |
| -------------------- | --------------------------------------- | -------------- | ---------------------------------- |
| FKVMP                | VMProtect 1.x–2.09                      | OllyDbg 插件     | Handler 识别、PCODE 还原；单基本块后停在 SetEIP |
| VMP 分析插件（zdhysd）     | VMProtect 1.x–2.09                      | OD/Immunity 插件 | 跨基本块提取、虚拟指令调试、表达式化简、字节码 patch、模板   |
| VMSweeper            | VMProtect 2.x / Code Virtualizer        | OllyDbg 插件     | 尝试还原 x86；稳定性差，日志在 `VMS_xxx/*.log`  |
| Oreans UnVirtualizer | Code Virtualizer/Themida/WinLicense 早期版 | OllyDbg 插件     | Oreans 系列 x86 还原；新版 FISH/TIGER 效果差 |
| VMAttack             | VMProtect                               | IDA 插件         | 伪代码还原/动静态分析；主要支持 demo              |
| VirtualDeobfuscator  | 通用                                      | Python         | Trace 化简（BlackHat 2013）            |

其他资源：VMP 1.7 完整还原文章、VMP Handler 插件、VMPDBG2、CV 反编译、CodeDeobfuscator，以及会议 PPT/论文（见仓库 `文章篇`）。

现实预期：这些工具大多针对旧版本/特定样本，VMProtect 3.x+ 的虚拟化结构变化、变异、反调试会显著降低自动化效果。流程应是：DIE 确认保护 → x64dbg 定位 VM 入口/派发器 → trace/Handler 识别 → 语义化简 → 人工验证。不要声称“一键脱 VMP”。

## 9. ReverseTool 工具索引

`weixinbao/ReverseTool` 是跨平台工具清单，适合按目标选择工具：

- **Java/JAR/Android**：jd-gui、Luyten、jadx-gui、Apktool、dex2jar、AXMLPrinter、androguard、Enjarify、ClassyShark、APK Analyzer、smali/baksmali、Smali2Java、CodeInspect、BytecodeViewer、JEB、radare2、Simplify、JAD、Introspy、ApkStudio、APK DeGuard。
- **Hook**：Xposed、Cydia Substrate、ADBI/DDI、Frida、Diff-GUI。
- **C++/.so**：IDA Pro、Frida、Ghidra、SoFixer、unicorn、unidbg、Binary Ninja。
- **C#/.NET**：ILSpy、.NET Reflector + Reflexil、Dependency Walker、dotPeek、de4dot、DILE、ilasm/ildasm、Just Decompile、Dotfuscator/ConfuserEx（混淆器）、OllyDbg。
- **iOS**：IDA、Hopper、Reveal/PonyDebugger、iFunbox/iExplorer/iTools、Charles、Cycript、LLDB、snoop-it、Introspy、class-dump、Theos、iOSOpenDev。
- **参考**：看雪、iOS 安全 Wiki、Android 安全中文站等。

工具可能过时/停止维护；优先选活跃项目（Ghidra、Frida、jadx、apktool、radare2/rizin、x64dbg）。

## 10. 格式与语言要点

- **PE**：DOS/NT 头、节区、导入/导出、重定位、TLS 回调、资源、overlay、Authenticode。`pefile` 快速脚本化；Ghidra/x64dbg 深入。
- **ELF**：`readelf -h/-S/-s/-d`、`objdump -d`、PLT/GOT、init_array、符号版本。
- **Mach-O**：`otool`/`jtool2`/`MachOView`、Fat binary、LC_LOAD_DYLIB、Objective-C 运行时。
- **.NET**：dnSpy/ILSpy、de4dot 去混淆、IL 修补；注意强名称/签名。
- **Go**：符号丰富时直接恢复函数名；strip 后用 GoReSym 等。
- **Rust**：符号/panic 字符串/`rustc` 版本；反编译可读性差，优先动态分析。
- **固件**：binwalk 提取、熵分析、文件系统、架构识别；在隔离环境进行。

## 11. 动态分析与补丁纪律

- 在 VM 快照中运行；记录网络、文件、注册表、进程行为。
- 先只读（string/import/trace），再考虑写内存/注入；所有写操作先备份并可回滚。
- 补丁输出到新文件，记录原始/补丁 SHA-256、偏移、preimage、验证结果。
- 不绕过许可证/DRM/付费墙；不做未授权的持久化、提权或横向移动。
- 恶意样本分析：断网、禁用共享目录、使用专用分析账号；样本与报告按机密数据管理。

## 12. 交付检查清单

- [ ] 样本哈希、来源、授权、分析环境记录
- [ ] 文件类型/架构/编译器/保护壳结论有证据
- [ ] 静态分析（函数/字符串/导入/资源）与动态行为分离记录
- [ ] 反编译/反汇编关键函数带地址与截图/文本
- [ ] 补丁/注入有回滚计划和验证；未覆盖原件
- [ ] VMP/加壳结论说明工具版本与局限，不夸大
- [ ] 报告脱敏，不含密钥/凭据；恶意样本不随报告外发
