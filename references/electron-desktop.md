# Electron / 桌面应用逆向

覆盖来源：`electron/asar`、`jonmest/How-To-Tamper-With-Any-Electron-Application`、`parsiya/evil-electron`、`fmartini23/electron-dev-tools`、`frida/frida`、`dslsdzc/rev-skills`（re-electron，skills.rest 镜像）、`cuddlesgiggles/minimax-design-auth`、`itsKayWat/Exe-Decompiler`（能力映射）。

> 

## 1. 快速识别

Electron 应用目录通常长这样：

```
App/
├── App.exe                 # Electron 启动器（Chromium + Node）
├── resources/
│   ├── app.asar            # 应用代码归档
│   └── app.asar.unpacked/  # 原生模块等未打包文件
└── ...
```

```bash
# 目录特征
ls resources/
# 二进制/版本线索
strings App.exe | grep -i -E 'electron|chrome' | head
# 归档摘要（纯 Python，无需 npm）
python scripts/asar_tool.py info resources/app.asar
python scripts/asar_tool.py list resources/app.asar | head -40
# 检查 Electron fuses（需要 Node）
npx @electron/fuses read --app /path/to/App.exe
```

判断依据：存在 `resources/app.asar`（或 `resources/app/`）、多进程（主进程 + GPU/渲染进程）、二进制内含 Electron/Chromium 版本串。应用 `--version` 往往没有输出；可靠版本在运行时用 CDP 执行 `process.versions` 获取。

## 2. ASAR 解包

### 2.1 官方 CLI

```bash
npm install -g @electron/asar        # Node >= 22.12
asar list app.asar
asar extract app.asar out/
asar extract-file app.asar package.json
asar pack out/ app.asar --unpack-dir "{**/*.node,**/node_modules}"
```

`--unpack-dir` 命中的文件写到 `app.asar.unpacked/`，运行时从磁盘加载。

### 2.2 纯 Python 工具（本技能自带）

```bash
python scripts/asar_tool.py list app.asar
python scripts/asar_tool.py info app.asar
python scripts/asar_tool.py cat app.asar package.json
python scripts/asar_tool.py extract app.asar out/ --path "out/main" --verify
python scripts/asar_tool.py extract app.asar out/ --path "*.node" --force
```

能力与官方 CLI 对齐：列表、整包/子集提取、单文件读出、SHA-256 完整性校验、`app.asar.unpacked` 处理、链接解析、路径穿越防护。

### 2.3 格式（需要手写解析时）

```
bytes 0..3   uint32 pickle payload size（通常 4）
bytes 4..7   uint32 header pickle size
bytes 8..    header pickle = uint32 payload size + uint32 JSON length + JSON
data start   = 8 + header pickle size
file offset  相对于 data start
```

JSON 目录形如：

```json
{"files":{"main.js":{"offset":"0","size":1234,"integrity":{"algorithm":"SHA256","hash":"...","blockSize":4096,"blocks":["..."]}},"x.node":{"unpacked":true}}}
```

重复内容可能共享同一 `offset`（去重）；`offset` 是字符串以保精度；`integrity` 是整文件 SHA-256 与分块哈希。完整性校验开启时，随便替换 `app.asar` 会导致启动失败。

## 3. 重打包 / 修改（授权场景）

标准流程（来自 How-To-Tamper 与 evil-electron）：

```bash
cp resources/app.asar resources/app.asar.bak
asar extract resources/app.asar app_unpacked
# 修改 app_unpacked/...（补丁、日志、IPC 观测等）
asar pack app_unpacked modified.asar --unpack-dir "{**/*.node,**/node_modules}"
cp modified.asar resources/app.asar
```

要点：

1. 先 `npx @electron/fuses read --app App.exe` 检查 `EnableEmbeddedAsarIntegrityValidation` 与 `OnlyLoadAppFromAsar`。前者开启时替换归档会失败；后者开启时只接受 asar 加载。此时优先做运行时插桩（Frida/CDP），不要硬改。
2. 写入 fuse 会改动可执行文件并破坏签名（macOS 需重新签名）；这是最后手段。
3. `evil-electron` 展示了 preload 注入：修改 `preload.js` 即可在渲染进程获得 Node 能力，无需 `nodeIntegration`。现代 Electron 默认 `sandbox: true`、`contextIsolation: true`，preload 的 Node 能力受限，需要结合目标配置判断。
4. 修改后的应用只在你控制的隔离环境中运行；不要分发修改后的第三方二进制。

## 4. re-electron 完整工作流

来源：`dslsdzc/rev-skills/.claude/skills/re-electron/SKILL.md`。核心原则：静态解包可免沙箱；运行应用、连 CDP、加载 `.jsc` 一律按动态样本处理（VM + 网络隔离）。

### 4.1 工具准备

| 工具                        | 安装                                  | 用途             |
| ------------------------- | ----------------------------------- | -------------- |
| Node.js + npm             | 官方安装器 / nvm                         | 工具底座           |
| `@electron/asar`          | `npm i -g @electron/asar`           | ASAR           |
| `chrome-remote-interface` | 项目内 `npm i chrome-remote-interface` | CDP 客户端        |
| `bytenode`                | `npm i -g bytenode`                 | `.jsc` 编译/加载对照 |
| `@electron/fuses`         | `npm i -g @electron/fuses`          | fuse 读取/翻转     |
| Ghidra / IDA              | 官方发布 / 商业                           | `.node` 原生模块   |
| xvfb（Linux）               | `apt install xvfb`                  | 无显示环境          |

### 4.2 操作步骤

1. **识别与版本**：`ls resources/`、`strings App | grep -i -E 'electron|chrome'`。版本只在动态阶段可靠：CDP `Runtime.evaluate` 执行 `process.versions`。
2. **ASAR 解包**：见第 2 节。先 list，再 extract；单文件用 extract-file/cat。注意 `app.asar.unpacked/` 是磁盘上的原生模块。
3. **主进程入口**：读 `out/package.json` 的 `main` → 主进程 JS。主进程是 Node 环境：`require` 链、`app/BrowserWindow/ipcMain` 即业务骨架。先列全 `ipcMain.handle/on`，这是主/渲染通信枢纽。不依赖 Electron API 的逻辑可用 `ELECTRON_RUN_AS_NODE=1 App.exe script.js` 离线复用（先确认 `RunAsNode` fuse 未关闭）。
4. **渲染进程 JS**：确定 BrowserWindow 的 `loadFile/loadURL` → 找入口 HTML → bundle → 美化/字符串定位 → 混淆层走 `references/js-web-reverse.md`。用硬编码密钥、API 域名、特征常量作锚点。
5. **原生 `.node`**：定位 `app.asar.unpacked/**/*.node`；`file`/`readelf -h` 确认 ELF/Mach-O/PE 与架构；用 Ghidra/IDA/radare2 分析。`NODE_MODULE_VERSION` 与 Electron 版本对应，可辅助确认版本。从导出表 + JS 调用点交叉定位业务函数。
6. **动态 CDP**：
   
   ```bash
   App.exe --inspect=9229              # 主进程 Node Inspector
   App.exe --inspect-brk=9229          # 启动即暂停
   App.exe --remote-debugging-port=9222  # 渲染进程 Chromium CDP
   curl -s http://127.0.0.1:9222/json/list
   ```
   - `EnableNodeCliInspectArguments` fuse 关闭时 `--inspect` 被忽略；改用渲染进程 CDP 或 Frida。
   - 浏览器页面连 CDP 受 Origin 检查（Chrome 111+）：加 `--remote-allow-origins=*`；Node 客户端无 Origin 头不受影响。
   - `chrome-remote-interface` 连 `webSocketDebuggerUrl` 后可 `Runtime.evaluate`、`Console.enable`、`Page.captureScreenshot`。
   - 单实例锁：加 `--user-data-dir=<新目录>` 或先结束现有实例。
   - 端口以 `/json/list` 实际响应为准；窗口未创建时 target 不出现，先触发 UI。
   - Linux 无显示：`xvfb-run -a App.exe`。
7. **反调试与数据提取**：常见检测包括 `process.argv/execArgv` 查 inspect 参数、`outerWidth - innerWidth` 查 DevTools、`debugger` 语句、版本异常校验。定位后 patch 或运行时 hook。注入面由 `contextIsolation`、`sandbox`、`nodeIntegration` 决定；CDP evaluate 要选对执行上下文（主 world vs 隔离 world）。日志：`ELECTRON_ENABLE_LOGGING=1` 或 `--enable-logging`。

### 4.3 关键陷阱

- **`.jsc` 是 V8 字节码快照**，不是 JS 文本；无公开反编译器。必须同 V8 版本、同平台编译才能加载。`Function.prototype.toString()` 被替换为桩是识别特征。能加载就跑行为分析（strace/网络/内存）；需要源码语义就找未编译副本或 sourcemap。Electron 42+ 主进程 `.jsc` 需 bytenode `electronMain` 模式编译。
- **ASAR 路径混淆与完整性**：按 JSON 的 size/offset 还原，不按路径语义；改包前先读 fuses。
- **`ELECTRON_RUN_AS_NODE` 差异**：该模式只提供 Node 运行时，无 Electron API；`RunAsNode` fuse 关闭时完全忽略。
- **contextIsolation / sandbox**：Electron 12+ 默认 contextIsolation true，20+ 默认 sandbox true。CDP 求值先 `Runtime.enable` 枚举 contextId。
- **fuses**：`--inspect`、`ELECTRON_RUN_AS_NODE` 都可能被关闭；写入 fuse 破坏签名。优先换 Frida/渲染 CDP。
- **单实例锁与端口**：独立 `--user-data-dir`；先触发 UI 再枚举 target。

## 5. Frida（跨平台动态插桩）

```bash
pip install frida-tools frida
frida-ps -U                       # USB 设备进程
frida-ps -D <device-id>
frida -U -f com.example.app -l hook.js --no-pause   # spawn 并注入
frida -U -n App.exe -l hook.js                     # attach 按名称
frida-trace -U -f App.exe -i "CreateFile*"
```

最小 hook 模板：

```javascript
// 观察主进程加载的模块与关键 API
const Module = Process.getModuleByName('electron.exe');
console.log('base', Module.base);
const fs = require('fs');
const open = fs.openSync;
Interceptor.replace(open, new NativeCallback(function (path, flags, mode) {
  console.log('[open]', path);
  return open(path, flags, mode);
}, 'int', ['pointer', 'int', 'int']));

// 观察 Node 模块（渲染/主进程均可，取决于注入点）
const ModuleCtor = Process.getModuleByName;
try {
  const { BrowserWindow } = require('electron');
  console.log('BrowserWindow', BrowserWindow);
} catch (error) {
  console.log('not an Electron main-process context', error.message);
}
```

要点：

- Electron 多进程：`frida-ps` 里会有多个同名进程；按 PID attach，或用 `frida -f` spawn 主进程。
- 主进程是 Node/V8，渲染进程是 Chromium/V8；Frida 注入点不同，能看到的全局对象不同。
- 配合 `frida-trace` 做 API 清单，再写针对性 hook。
- Windows 上 Frida 可能被反调试/EDR 拦截；只在授权环境使用。

## 6. IPC / 日志观测（electron-dev-tools）

```bash
npm install --save-dev electron-dev-tools
```

```javascript
const { app, BrowserWindow } = require('electron');
const { initializeDevTools } = require('electron-dev-tools');

app.whenReady().then(() => {
  const win = new BrowserWindow({ /* ... */ });
  win.loadFile('index.html');
  if (process.env.NODE_ENV !== 'production') initializeDevTools();
});
```

它通过 monkey-patch `console`、`ipcMain` 把主进程和各渲染进程日志、IPC 消息汇总到一个 React 窗口。适合在你可修改源码/可重打包的授权测试中观察 IPC 通道、payload 与方向（send/invoke）。

对不可修改的二进制：优先 CDP（渲染侧）+ Frida（主进程侧）；IPC 消息可在 preload/主进程 hook `ipcMain.emit` 或 `webContents.send`（需要确认模块与调用点）。

## 7. `.jsc`（bytenode）边界

```bash
npm i -g bytenode
bytenode -c main.js            # 生成 main.jsc
bytenode -e main.js            # 为 Electron 编译
bytenode -ep /path/to/electron main.js
```

```javascript
// Electron 42+ 主进程
require('bytenode').compileFile({ electronMain: true, filename: 'main.js' });
```

- 用目标同版本 Electron/Node 重编译样本 `.jsc`，对照魔数与可加载性；这不是反编译。
- 版本不匹配会直接崩溃；`node --print-bytecode` 只打印运行中编译字节码，不还原源码。
- 分析策略：同版本加载后观察行为（文件、网络、内存、IPC），或寻找未编译的 `.js`/sourcemap。

## 8. 案例：MiniMax Design（Hilo）登录态

来源：`cuddlesgiggles/minimax-design-auth`。这是“Electron 桌面登录态 + 本地加密缓存”的典型案例，仅用于互操作/自有账号研究。

登录态位置：

- Windows：`%APPDATA%\@hilo\desktop\hub-config.json`
- macOS：`~/Library/Application Support/@hilo/desktop/hub-config.json`
- Linux：`~/.config/@hilo/desktop/hub-config.json`

`tokens.accessToken` 是 `v2enc:<iv>:<tag>:<cipher>` 信封（AES-256-GCM），密钥为同目录 `.token-key` 的 32 字节原始内容。解出的是 HS256 JWT（`exp`、`user{id,name,avatar,deviceID,isAnonymous}`），约 38 天过期；文件里没有 refresh token。

模型与积分接口（供互操作分析）：

- `GET https://design.minimax.cn/api/v1/config`，`token:` 头，无签名；按 `enabled_providers` 顺序展开。
- `GET /api/v1/credit/wallet`、`GET /api/v1/credit/balance`，`token:` 头，数字为字符串。

分析要点：先定位配置文件与 `.token-key`，确认 envelope 结构，再验证 JWT 声明；不要把 token 写入报告或日志。使用必须遵守服务条款，仅限自己的账号。

## 9. Exe-Decompiler 能力映射

`itsKayWat/Exe-Decompiler` 是闭源付费 Windows GUI，提供二进制分类、ASAR 解包、PyInstaller 解包、PE 头/资源、source map、结果浏览。用本技能的开源等价流程即可完成：

| Exe-Decompiler 能力 | 开源替代                                             |
| ----------------- | ------------------------------------------------ |
| Electron ASAR     | `scripts/asar_tool.py` / `@electron/asar`        |
| PyInstaller       | `pyinstxtractor.py` / `MrWQ/reverse_pyinstaller` |
| PE 头/节区/导入        | DIE、`pefile`、Ghidra、x64dbg                       |
| 文件类型/框架           | DIE `diec`                                       |
| Source map        | `source-map` / `js-beautify` / DevTools          |
| GUI 浏览            | Ghidra、Cutter/rizin、x64dbg                       |

## 10. 交付检查清单

- [ ] 目标、授权范围、样本 SHA-256 已记录
- [ ] 原始归档与解包目录分别保存，未覆盖原件
- [ ] 版本（Electron/Chromium/V8/Node/modules）来自运行时证据
- [ ] 主进程入口、IPC handler、渲染 bundle、原生模块清单完整
- [ ] 动态调试端口/进程/上下文明确；结论标注“事实/推断”
- [ ] 未在报告中泄露 token、Cookie、密钥；必要时脱敏
- [ ] 修改/重打包只在隔离环境进行，未分发第三方二进制
