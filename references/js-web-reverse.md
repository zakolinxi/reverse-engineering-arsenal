# Web / JavaScript 逆向

覆盖来源：`wuji66dde/jshook-skill`、`erma0/js-reverse-skill`、`WhiteNightShadow/hello_js_reverse_skill`、`715494637/reverse-skill`、`zhizhuodemao/js-reverse-mcp`、`kuizuo/js-deobfuscator`、`JiangtaoQu/js-reverse-evolver`、`WhiteNightShadow/firefox-reverse`、`LoseNine/Firefox-FingerPrint-Analyzer`（RuyiTrace，原仓库已删除）、`Evil0ctal/Reverse-Engineering-Online-Toolkit`。

> 

## 1. 证据模型（先证据，后结论）

一个可交付的 JS 逆向结论必须能回答：

1. **目标请求**：完整 URL、方法、headers、body、触发动作。
2. **动态字段**：`sign`/`token`/`cookie`/`deviceId` 等字段的真实 writer、builder、sink。
3. **运行时事实**：调用栈 `file:line:col`、入参、返回值、中间态、时序。
4. **环境依赖**：navigator/screen/document/Canvas/WebGL/Audio/WebCrypto/performance/worker/iframe 等读取。
5. **验证样本**：固定输入 → 输出/中间态与浏览器逐字节/逐值对齐。
6. **交付**：纯 Node/Python 实现，至少 5 次真实请求验证通过（或明确说明无法完成的原因）。

严格区分“日志中看到的”“推断的”“未覆盖的”。不要把 4000 字符的截断日志当成真实长度。

## 2. 通用工作流

### Phase 0 — 环境与授权

- 记录目标、账号、授权范围、时间窗口；确认允许自动化和抓包。
- `python scripts/env_probe.py` 检查 Node/Python/浏览器/mitmproxy/Frida。
- 优先使用有头浏览器 + 独立 profile；取证工具版本固定，避免指纹基线漂移。

### Phase 1 — 静态定位

1. 页面源码/JS 列表：URL、source map、webpack chunk、worker、WASM。
2. 搜索锚点：字段名、`sign`、`encrypt`、`token`、`nonce`、`timestamp`、`X-*`、API path。
3. 用 `python scripts/js_triage.py <bundle.js> --out triage.md` 生成混淆/加密/端点分诊。
4. 美化大 bundle（js-beautify/SourceMap）；保留原始文件与哈希。

### Phase 2 — 动态取证

- **网络证据**：mitmproxy（见 `network-capture.md`）、浏览器 Network、js-reverse-mcp、RuyiTrace。
- **调用栈**：XHR/fetch breakpoint，或 `get_request_initiator`；拿到 writer 所在脚本与行号。
- **运行时数值**：断点处读取局部变量、闭包、原型链、descriptor、`toString`。
- **环境读取日志**：RuyiTrace（C++ 内核层，JS 不可见）或注入 hook（可被检测）。

### Phase 3 — 定位 write 边界

对目标字段回答：

- 谁最后写入请求（writer）？
- 谁构造中间对象（builder）？
- 谁把值放上网络（sink）？
- 值是否来自 Cookie、localStorage、服务端下发、WASM、worker？
- 正常链路与风控链路在哪里分叉？

### Phase 4 — 还原

按依赖从低到高：

1. 标准算法（MD5/SHA/HMAC/AES/RSA/SM4/RC4…）→ 直接重写。
2. 自定义变换（XOR、字符表、编码、时间戳、随机数）→ 用固定输入对拍。
3. OB 混淆 / 控制流平坦化 → AST 去混淆。
4. JSVMP → 黑盒执行 / 最小环境 / 指令 trace / eval 源码落盘。
5. WASM → 加载、import 边界、反汇编、调用导出函数。
6. 浏览器/指纹依赖 → 补环境或纯算重建。

### Phase 5 — 验证

- 固定样本至少 5 条，逐字段比较；必要时比较中间态。
- 签名结果一致 ≠ 请求成功：还要验证 headers、Cookie、时间戳、TLS/HTTP2 指纹、请求顺序。
- 失败时按“请求失败排查”清单逐项排除：Cookie、Header、时间戳、nonce、签名、body 编码、重放限制。

### Phase 6 — 交付

默认目录（来自 `erma0/js-reverse-skill`）：

```
result/
├── final.js / final.py          # 唯一执行入口
├── config.json                  # 外置配置（脱敏）
├── package.json / requirements.txt
├── 最终项目总结.md
├── 经验沉淀-<站点>.md
├── 验证记录.json
└── src/
    ├── signer.js                # 签名
    ├── env/                     # 补环境（如需要）
    └── request/                 # 请求客户端
```

要求：纯协议、无浏览器自动化依赖（除明确选择浏览器交付）、至少 5 次真实请求验证、报告不包含 token/密钥。

## 3. 工具路由

| 场景                              | 首选                        | 备选                             |
| ------------------------------- | ------------------------- | ------------------------------ |
| 真实 Chrome 调试、断点、网络/WS、保存源码      | `js-reverse-mcp`          | Chrome DevTools / jshook-skill |
| 需要 C++ 引擎级、不可被页面 hook 干扰的 trace | RuyiTrace                 | Firefox-Reverse                |
| 大型混淆 AST 还原                     | `js-deobfuscator`         | jshook-skill 的 AI 反混淆          |
| 一体化 AI 工作流 + 多工具                | `hello_js_reverse_skill`  | `715494637/reverse-skill`      |
| 请求链/写边界/交接文档                    | `715494637/reverse-skill` | `erma0/js-reverse-skill`       |
| 自进化去混淆                          | `js-reverse-evolver`      | —                              |
| 快速编码/哈希/加密转换                    | REOT                      | CyberChef                      |
| 内置 AI 的 Firefox 工作站             | Firefox-Reverse           | RuyiTrace + ruyipage           |

## 4. js-reverse-mcp（AI-native Chrome MCP）

- 要求 Node >= 20.19 + Chrome。安装：MCP 配置 `{"command":"npx","args":["js-reverse-mcp"]}`；Claude Code：`claude mcp add js-reverse npx js-reverse-mcp`。
- 默认：有头 Chrome、持久化 profile、专用 Patchright fork、CDP 静默导航、真实视口、Google referer。
- Flags：
  - `--isolated`：临时 profile，排除残留状态。
  - `--cloak`：CloakBrowser 源码层指纹补丁（首次约 200MB，先 `npx cloakbrowser install`）。
  - `--browserUrl/-u http://127.0.0.1:9222`：连接已运行 Chrome / 指纹浏览器 CDP endpoint（不接受厂商私有 API）。
  - `--allowedRoots`：限制本地文件读写目录，强烈建议。
  - `--logFile`：调试日志；不要用 `DEBUG=*`，会泄露页面/凭据。

24 个工具（按用途）：

| 组     | 工具                                                                                                                        |
| ----- | ------------------------------------------------------------------------------------------------------------------------- |
| 页面    | `select_page` `new_page` `navigate_page` `select_frame` `click_element` `take_screenshot`                                 |
| 脚本    | `list_scripts` `get_script_source` `save_script_source` `search_in_sources`                                               |
| 断点    | `set_breakpoint_on_text` `break_on_xhr` `remove_breakpoint` `list_breakpoints` `get_paused_info` `pause_or_resume` `step` |
| 网络/WS | `list_network_requests` `clear_network_requests` `get_request_initiator` `get_websocket_messages`                         |
| 状态/执行 | `clear_site_data` `evaluate_script` `list_console_messages`                                                               |

推荐捕获流程（导航阶段故意 CDP 静默）：

```
1. new_page 打开目标
2. list_network_requests 激活 collectors
3. navigate_page(type="reload") 刷新
4. list_network_requests 看完整请求
5. 对关键 reqid 用 outputFile 导出原始材料
```

Cookie/风控重放：

```
1. clear_site_data(confirm=true)
2. navigate_page(type="reload")
3. 找 Set-Cookie / sensor 请求
4. 导出 requestBody/responseHeaders/responseBody
5. evaluate_script + localFilePath 复算/验证
```

安全：`evaluate_script.localFilePath` 和 `outputFile` 会读写宿主机；生产环境必须 `--allowedRoots`。

## 5. jshook-skill 命令速查

安装：`git clone ... && npm install && npm run build`；`.env` 配 OpenAI/Anthropic Key（AI 功能需要），Node >= 18。

| 能力       | 命令                                                                                                                              |
| -------- | ------------------------------------------------------------------------------------------------------------------------------- |
| 收集代码     | `collect <url> [--smart-mode=summary                                                                                            |
| 搜索       | `search "X-Bogus" --context=10`；`search "function.*encrypt" --regex --max-matches=50`                                           |
| 反混淆/理解   | `deobfuscate <code>`、`understand <code> --focus=security`、`summarize collected --batch`                                         |
| 加密检测     | `detect-crypto <code>`                                                                                                          |
| 浏览器      | `browser launch                                                                                                                 |
| 调试器      | `debugger enable                                                                                                                |
| 断点       | `breakpoint set-url <url> <line> [cond]`、`breakpoint set-script`、`breakpoint list/remove/clear`                                 |
| 脚本       | `script list                                                                                                                    |
| 监视       | `watch add/list/evaluate/remove/export/import/clear`                                                                            |
| XHR/事件断点 | `xhr-breakpoint set */api/*`；`event-breakpoint set click                                                                        |
| Blackbox | `blackbox set *jquery*.js`、`blackbox set-common`                                                                                |
| Hook     | `hook generate function encryptData                                                                                             |
| 反检测      | `stealth inject`、`stealth inject-preset windows-chrome                                                                          |
| DOM/页面   | `dom query/structure/clickable/style/wait`；`page navigate/click/type/select/hover/scroll/wait-selector/eval/screenshot/metrics` |

16 项 stealth：hideWebdriver、mockChrome、canvasNoise、webglVendor、audioNoise、navigatorProps、permissionsAPI、batteryAPI、mediaDevices、notifications、networkInfo、hasFocus 等。仅用于授权的反检测研究，不用于欺诈/大规模绕过。

## 6. hello_js_reverse_skill（双语言交付 + Camoufox MCP）

核心：API 采集、签名分析、JSVMP、WASM、动态 Cookie、协议层对抗、反检测浏览器；Node/Python 双路径。

- 安装：克隆到 `.cursor/skills/`、`.codex/skills/` 或 `.vscode/skills/`；`bash scripts/check-deps.sh`。
- 脚本：
  
  ```bash
  node scripts/crypto-identifier.js "e10adc3949ba59abbe56e057f20f883e"
  node scripts/hook-generator.js --type=cookie
  node scripts/hook-generator.js --type=xhr --target="/api/data"
  node scripts/hook-generator.js --type=all
  node scripts/sandbox-runner.js obfuscated.js --extract-cookie --verbose
  ```
- 模板：
  - `templates/node-request/`：标准算法纯算
  - `templates/python-request/`：Python 纯算
  - `templates/vm-sandbox/`：eval/动态 Cookie
  - `templates/wasm-loader/`：WASM 加载与补环境
  - `templates/browser-auto/`：无法脱离浏览器
- Camoufox MCP 关键工具：`launch_browser`、`navigate`、`search_code`、`scripts`、`evaluate_js`（main/isolated）、`hook_function`、`inject_hook_preset`、`hook_jsvmp_interpreter`、`instrumentation`（AST 源码级插桩）、`network_capture`、`get_request_initiator`、`intercept_request`、`cookies`、`compare_env`、`trace_property_access`、`verify_signer_offline`、`export_state`。
- 场景速查：签名（MD5/HMAC/自定义）、动态 Cookie、响应 AES/DES/RC4、OB/CFF、JSVMP、自定义 VM、WASM、TLS 指纹（curl_cffi/curl-impersonate）、HTTP/2、字体反爬、WebSocket、反调试、环境检测、Cloudflare/RS/JY（授权场景）。

## 7. 715494637/reverse-skill（证据化请求链）

安装：接入 js-reverse-mcp，把 `jsr-reverse` 目录复制到技能根目录。

核心流程：

1. **请求链证据化**：目标请求、触发动作、上游依赖、状态消费、正常/风控分叉。
2. **写边界证明**：动态字段、请求头、Cookie、消息对象的真实 writer/builder/sink。
3. **壳层恢复**：JSVMP、AST、worker、WASM、webpack/runtime、协议包络、桥接层。
4. **运行时对齐**：对象、状态、时序、生命周期、指纹、风控分支。
5. **检查点验证**：固定样本，对齐输入/输出/中间态/状态依赖。

交接文档：`reverse-records/请求链路.md`，包含请求区块、运行时补充、恢复补充、验证补充。会话中断后先更新该文档，再继续。

推荐 prompt 必须包含：URL、接口/字段、触发方式、当前现象、Cookie 约束、是否允许补环境、是否纯算法、交付语言。

## 8. js-deobfuscator（AST 自动化）

```bash
git clone https://github.com/kuizuo/js-deobfuscator
cd js-deobfuscator && pnpm install
pnpm exec deob path/to/input.js -o ./out
cat input.js | pnpm exec deob > output.js
```

```ts
import { deob } from 'deob';
const { code, save } = await deob(source, {
  decoderLocationMethod: 'callCount',
  decoderCallCount: 300,
  mangleMode: 'hex',
});
await save('./out');
```

能力：decoder 发现（字符串数组长度/调用次数/手动指定）、字符串数组与 rotator、控制流平坦化恢复、死代码消除、对象属性合并、反自保护/反调试、变量重命名（hex/short/custom）、CLI/Playground/API。适用于 OB 类混淆；对依赖运行时状态的 VM 需要动态 trace 配合。

## 9. js-reverse-evolver（自进化 MCP）

```bash
npm install
npx playwright install chromium
cp .env.example .env   # 填 MemOS / js-reverse-mcp 地址
npm run build && npm start
```

MCP 配置示例：`{"command":"node","args":["/path/to/js-reverse-evolver/dist/index.js"]}`。

四个工具：

- `evolve_js`：目标 URL → 自动进化反混淆代码。
- `query_knowledge`：查询积累的模式/策略。
- `inject_knowledge`：人工注入混淆模式。
- `get_evolution_status`：引擎状态与统计。

自学习：成功特征写入 `knowledge/patterns.json`；命中 ≥3 次晋升到 `strategy_candidates.json`；下次启动加载。

## 10. Firefox-Reverse（内置 AI 的 Firefox 工作站）

- 下载 release（Windows/macOS/Linux），启动后打开侧边栏，配置模型（DeepSeek/GLM/Kimi/MiniMax/Qwen/Claude/OpenAI 或兼容端点）。
- 两种模式：全自动一条龙；AI 辅助逐阶段（人类或 MCP director 领航）。
- 二阶段路线：**黑盒可用**（Node 补环境跑原 WASM/JSVMP，实打接口成功）→ **白盒纯算**（重写算法，不依赖原始二进制）。
- 71 个工具（按类别）：
  - 页面自动化 12：navigate/click/scroll/type/eval/screenshot/elements/info/automation_scan/frames/snapshot/find
  - 网络/入口 5：net_capture、net_list、net_get、hook_inject、find_param_entry
  - 代码 4：code_search、scripts_list、scripts_save、scripts_capture_all
  - 签名器/闭包 2：signer_trace、closure_read
  - WebAPI trace 2：webapi_trace、webapi_query
  - JSVMP 5：jsvmp_trace、jsvmp_query、jsvmp_status、jsvmp_split_dispatcher、jsvmp_disassemble
  - 密码学 1：crypto_scan
  - WASM 2：wasm_probe、wasm_disasm
  - 白盒诊断 1：whitebox_diff
  - 通用 JS trace 1：js_trace
  - 执行/文件 8：run_node、run_python、npm_install、fs_read/write/list/copy/mkdir
  - Cookie 1、扩展 2、Skills/记忆 7、指纹环境 18
- 指纹环境：一个环境 = 独立 profile + 独立进程 + 独立 Marionette 端口；`~/.firefox-reverse/environments`；支持 fingerprint.json 导入。
- 引擎级观测：signer_trace、jsvmp_trace、wasm_probe、whitebox_diff 深入 SpiderMonkey/Gecko C++ 层，减少页面内 hook 被检测的风险。
- MCP director：`frx-director-mcp` 可用强模型指挥浏览器内 worker 模型（成本拆分）。

## 11. RuyiTrace（原 Firefox-FingerPrint-Analyzer）

**状态**：原仓库 `LoseNine/Firefox-FingerPrint-Analyzer` 已 404（2026-10-21）。其完整能力文档、采集脚本和 NDJSON 导入工具保存在 `erma0/js-reverse-skill` 中：`erma0/js-reverse-skill/references/tooling/ruyi-tooling.md`、`erma0/js-reverse-skill/references/tooling/ruyitrace-cheatsheet.md`、`erma0/js-reverse-skill/scripts/capture_ruyitrace_log.js`、`erma0/js-reverse-skill/scripts/import_ruyitrace_log.js`。不要下载来源不明的同名第三方包。

定位：Windows x64 桌面工具，随包定制 Firefox trace 内核，在 **C++/Gecko 引擎层**记录 DOM/JS API 调用到 NDJSON。相比页面内 JS hook，页面脚本无法通过原型检测/toString 嗅探发现探针，适合高保真补环境与指纹分析。

### 11.1 典型能力

- 核心 DOM/BOM trace、jscall（函数入参/返回值）、opcode/JSVMP、WASM dump、WebSocket 帧、Cookie/Storage、事件、异常、eval 源码落盘。
- 定向开关，避免 GB 级日志；`TRACE_GATE` 支持运行时开/关窗口。
- 指纹基线：同一 profile/baseline 下采集 navigator/screen/Canvas/WebGL/Audio 等值。

### 11.2 采集流程

```bash
# 1) 安装 ruyiPage 与定制 Firefox runtime
python -m pip install ruyiPage requests --upgrade
python -m ruyipage install --install-dir <browsers-dir>
python -m ruyipage doctor --install-dir <browsers-dir>

# 2) 自动 trace（需要 RuyiTrace 安装，脚本在 erma0/js-reverse-skill）
node scripts/capture_ruyitrace_log.js --url <target> --case-dir <case> --ruyitrace-home <dir> --import-after --markdown

# 3) 手动导入
node scripts/capture_ruyitrace_log.js --input <trace.ndjson> --case-dir <case> --markdown
node scripts/import_ruyitrace_log.js --input <trace.ndjson> --case-dir <case> --truncation-threshold 3900 --markdown
```

手动启动环境变量（核心）：

```bat
set MOZ_DOM_TRACE=1
set MOZ_DOM_TRACE_FILE=<trace.ndjson>
set MOZ_DOM_TRACE_LIMIT=<n>
set MOZ_DISABLE_LAUNCHER_PROCESS=1
<ruyitrace-firefox.exe> -no-remote -new-instance <url>
```

关键定向开关：

| 场景           | 开关                                                                        |
| ------------ | ------------------------------------------------------------------------- |
| 只抓某脚本 jscall | `MOZ_DOM_JSCALL_TRACE=1` + `MOZ_DOM_JSCALL_SCRIPT_URL=target.js`          |
| 抓某函数参数/返回值   | `MOZ_DOM_JSCALL_DETAIL_FUNCS=encrypt,sign`                                |
| 抓整个脚本的真值     | `MOZ_DOM_JSCALL_DETAIL_SCRIPT_URL=target.js`                              |
| 看穿字节码 VM     | `MOZ_DOM_JSCALL_OPCODE_URL=target.js` + `STACK=1` + `OPERANDS=1` + PC 窗口  |
| JSVMP 自动识别   | `MOZ_DOM_JSVMP_TRACE=1` + `MOZ_DOM_JSVMP_SCRIPT_URL=...` + `AUTODETECT=1` |
| WASM         | 默认 dump；`MOZ_DOM_WASM_INSN=1` 指令级                                         |
| WebSocket    | `MOZ_DOM_WS_TRACE=1`                                                      |
| 运行时闸门        | `MOZ_DOM_TRACE_GATE=<control-file>`（存在=开，删除=关）                            |

纪律：

- `OPCODE_*`/`JSVMP_*` 必须锁单脚本，并设置 PC 窗口/上限；`STACK_FULL` 是 GB 级日志主因。
- 反爬/时延敏感站点不要禁用 JIT、不要深序列化；用 `SHALLOW=1`。
- NDJSON 字符串可能截断在 ~4000 字符：标记 `truncationSuspected`、`visibleLength`、`actualLength=unknown`，不得把可见值当真实值。
- `stack.file:line:col` 是定位权威依据，先按 API/参数缩小范围，再用行号切源码。

### 11.3 NDJSON 结构

```json
{"t":"call","api":"CanvasRenderingContext2D.fillText","args":["example",4,17],"stack":[{"file":"https://site/fp.js","line":42,"col":17}]}
```

导入后按 API 频率、调用栈聚合、模块分类（navigator/screen/storage/canvas/WebGL/audio/crypto/performance/worker/iframe）生成 `notes/ruyitrace-summary.md` 和补环境计划。

## 12. REOT（在线工具箱）

纯前端、Docker 可部署。适合快速转换与协议解析：

- 编码：Base64/Base32/Base58/URL/HTML/Unicode/Hex/ASCII/Punycode/ROT/Morse。
- 压缩：GZIP/Deflate/ZSTD/Brotli/LZ4。
- 哈希/HMAC/KDF：MD5/SHA-1/2/3/BLAKE2/CRC/RIPEMD/xxHash、HMAC、PBKDF2/bcrypt/HKDF。
- 加密：AES/DES/3DES/RC4/Blowfish/ChaCha20/SM4；RSA/ECC/SM2/Ed25519。
- 格式化：JSON/XML/YAML/TOML/CSV/SQL/HTML/CSS/JS/GraphQL。
- 二进制：Hex 查看/编辑、文件类型、字节序、字符串提取、XOR、频率分析、模式搜索、结构体、偏移。
- 协议：JWT、Protobuf、ASN.1、X.509、PEM、MessagePack、CBOR、Plist。
- 网络：Cookie/UA/HTTP 头/IP/URL、cURL 转代码、CIDR。
- 生成器：UUID、时间戳、条码、密钥对、Snowflake、ObjectID、ULID。
- 移动端：设备指纹格式、Deep Link（部分计划中）。

部署：`docker compose up` 或 `npx serve`；在线版见仓库 README。

## 13. 去混淆与恢复手册

### 13.1 常见混淆

| 类型                   | 特征                                | 策略                                   |
| -------------------- | --------------------------------- | ------------------------------------ |
| 字符串数组 + decoder      | `_0x...`、大数组、rotator              | 找 decoder、执行/替换调用、还原数组               |
| 控制流平坦化（CFF）          | `switch` + 状态变量 + 大循环             | AST 状态机还原、执行轨迹                       |
| eval/Function packer | `eval(function(p,a,c,k,e,d)...)`  | 解包器还原、格式化                            |
| 自保护/反调试              | `debugger`、`constructor`、计时检测     | 去自保护、条件断点、Hook                       |
| JSVMP                | 自定义字节码 + 解释器                      | 黑盒执行 / 最小环境 / opcode trace / eval 源码 |
| WASM                 | `.wasm`、`WebAssembly.instantiate` | 导出函数、import 边界、WAT 反汇编               |
| webpack/runtime      | `webpackChunk`、模块表                | 还原模块边界、运行时函数                         |
| worker               | `new Worker`、blob URL             | 单独抓 worker 脚本、消息协议                   |

### 13.2 AST 流程

1. 解析（Babel/esprima），保留注释/位置。
2. 常量折叠、字符串数组还原、decoder 内联。
3. 控制流状态机还原、死代码删除。
4. 变量/函数重命名（谨慎，保持引用一致）。
5. 反复多轮，每轮保存 diff；最终用真实样本验证。

### 13.3 JSVMP 路线

1. **黑盒优先**：把 VM 当黑盒，补最小环境执行，先拿到“能用”的签名。
2. **行为 trace**：RuyiTrace / Firefox-Reverse jsvmp_trace / 源码级插桩；记录 pc、opcode、操作数、栈。
3. **eval 源码**：部分 VM 在业务层用 eval 执行反序列化源码；RuyiTrace 会把 eval 源码落盘，可直接读业务逻辑。
4. **纯算**：还原 opcode 语义、常量表、密钥流；用逐位 XOR/差值分析定位环境差异。
5. **边界**：不要声称反编译了字节码源码；没有证据时标注“黑盒可用”。

### 13.4 WASM

- 从 Network/磁盘获取原始 `.wasm`（校验魔数 `\0asm` 与 SHA-256）；不要用被文本化损坏的抓包副本。
- `wasm2wat`/Ghidra WASM 插件/浏览器 DevTools 反汇编。
- 观察 imports/exports、内存读写、实例化参数；用 Node `WebAssembly` 加载并补 import。
- 若只依赖导出函数，黑盒调用往往比完全反编译更快。

## 14. 加密、协议与浏览器环境

- 标准算法重写：Node `crypto`/`crypto-js`/`node-forge`；Python `hashlib`/`hmac`/`pycryptodome`。
- TLS 指纹：`curl_cffi`（Python）、`curl-impersonate`、或真实浏览器；Node 原生 TLS 指纹不同。
- HTTP/2：Node `http2`、Python `httpx[http2]`；确认伪头顺序/设置。
- 动态 Cookie：Hook `document.cookie` setter、分析 eval 首包、api 预热、指纹 Cookie；用 Cookie 归因工具区分 Set-Cookie 与 JS 写入。
- 字体反爬：解析字体 CMAP、映射字形；保留原始字体与哈希。
- 验证码：只分析你自己系统的验证码封装层；不要针对第三方实施绕过。
- 请求失败排查：Cookie 是否完整、Header 顺序/大小写、时间戳单位、nonce 是否一次性、body 编码、签名输入是否含空格/中文、是否被重放限制、TLS/HTTP2 指纹、IP/地区。
- 补环境：优先用 RuyiTrace 证据；固化属性描述符、访问器、原型链、`toString`、`document.all` 等；每次补环境后用固定 fixture 校验。

## 15. 交付与反模式

交付前检查：

- [ ] `final.js`/`final.py` 可独立运行，无浏览器依赖（除非明确选择浏览器方案）
- [ ] 签名/加密函数有输入输出 fixture，≥5 条真实请求通过
- [ ] 配置外置、敏感值脱敏；日志不打印 token/cookie
- [ ] 报告区分事实/推断/未覆盖；有请求链与调用栈证据
- [ ] 处理了时间戳、随机数、Cookie、Header、TLS/HTTP2 等非算法因素

反模式：

- 只凭字符串搜索就断言算法；不看运行时。
- 用截断日志当真实值；用 AI 猜测指纹。
- 修改一个参数就宣称成功；不做多请求验证。
- 直接照搬上游案例到不同站点；忽略版本/构建差异。
- 在第三方站点上使用反检测/绕过手段进行未授权访问。
