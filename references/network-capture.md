# 网络拦截与协议取证

覆盖来源：`mitmproxy/mitmproxy`、`yakrsa/MiteProxy`、`Aillumine/mitmproxy-mcp`

## 1. 工具选择

| 需求                    | 工具                                         |
| --------------------- | ------------------------------------------ |
| 脚本化、可编程、CI/自动化        | mitmproxy（mitmdump + addon）                |
| 图形界面、Mock、重放、对比       | MiteProxy                                  |
| AI/MCP 查询流量、真机抓包      | mitmproxy-mcp                              |
| 非 HTTP（TCP/UDP/自定义协议） | tshark/Wireshark + `protocol` 分析           |
| 浏览器内请求                | DevTools Network / js-reverse-mcp（见 JS 参考） |

## 2. mitmproxy 基础

```bash
pip install mitmproxy
mitmproxy -p 8888                 # TUI
mitmweb -p 8888 --web-port 8081   # Web UI
mitmdump -p 8888                  # 命令行/脚本
mitmdump --version
```

客户端代理指向 `127.0.0.1:8888`（或宿主局域网 IP）。HTTPS 需要安装 CA：

1. 代理开启后，在被拦截设备浏览器访问 `http://mitm.it`。
2. 按平台下载证书：
   - Windows：安装到“受信任的根证书颁发机构”。
   - macOS：钥匙串 → 系统 → 始终信任。
   - Android：用户证书（Android 7+ 应用默认不信任用户 CA，见 6.1）。
   - iOS：安装描述文件 + 设置 → 通用 → 关于本机 → 证书信任设置。
3. 验证：访问 HTTPS 页面无证书错误，mitmproxy 中出现 flows。

### 2.1 常用命令

```bash
# 保存/回放
mitmdump -p 8888 -w traffic.mitm
mitmdump -r traffic.mitm --set flow_detail=3

# 过滤（mitmproxy 表达式）
mitmdump -p 8888 "~u example.com"
mitmdump -p 8888 "~m POST & ~u /api/"

# 只记录，不显示
mitmdump -q -p 8888 --set save_stream_file=stream.mitm

# 反向代理（客户端不需要设置代理）
mitmdump --mode reverse:http://127.0.0.1:8080 -p 8889

# 上游代理
mitmdump --mode upstream:http://upstream:3128 -p 8888

# 忽略某些主机（不拦截）
mitmdump --set ignore_hosts=example.com,*.internal

# 本地映射（不改服务端）
mitmdump --set map_local:/api/=http://127.0.0.1:9000/api/
```

常用 addon 事件：`load`、`request`、`response`、`http_connect`、`websocket_start`、`websocket_message`、`error`、`done`。脚本可读写 `flow.request/response`，也可用 `ctx.log` 输出。

### 2.2 本技能自带捕获 addon

```bash
RE_CAPTURE_OUT=flows.jsonl mitmdump -q -p 8888 -s scripts/mitm_capture.py
RE_CAPTURE_OUT=flows.jsonl RE_CAPTURE_HOSTS=api.example.com \
  mitmdump -q -p 8888 -s scripts/mitm_capture.py
```

环境变量：

| 变量                    | 作用                                     |
| --------------------- | -------------------------------------- |
| `RE_CAPTURE_OUT`      | JSONL 输出路径                             |
| `RE_CAPTURE_HOSTS`    | 逗号分隔的主机子串；空=全部                         |
| `RE_CAPTURE_BODIES`   | `1` 记录 body（默认）                        |
| `RE_CAPTURE_MAX_BODY` | 单 body 最大字节（默认 262144）                 |
| `RE_CAPTURE_REDACT`   | `1` 遮罩 Authorization/Cookie/Set-Cookie |

每条 JSONL 带 `event`（request/response/connect/ws_open/ws_message/error）、时间戳、URL、headers、body（UTF-8 或 base64）、耗时。适合后续用 `jq`/Python 做请求链与字段分析。

### 2.3 常见限制

- mitmproxy 只处理 HTTP/1.1、HTTP/2、WebSocket；原始 TCP/UDP 需 tshark。
- 证书固定（SSL Pinning）会使部分请求失败；在授权测试中可用 Frida 等动态插桩分析，不要在生产/第三方环境强行绕过。
- 某些 App 使用 QUIC/HTTP3，可能绕过 HTTP 代理；确认协议或禁用 QUIC。
- 双向 TLS / 客户端证书需要配置 `client_certs`。
- 大响应/流式响应不要一次性读入内存；用流式 addon 或分片读取。
- 不要在报告中记录完整 Cookie/Authorization；必要时用 `RE_CAPTURE_REDACT=1`。

## 3. MiteProxy（GUI，类 Fiddler）

基于 mitmproxy + PySide6；默认 `127.0.0.1:8888`。启动即自动接管系统代理，关闭自动还原。

能力：

- HTTP/HTTPS 抓包，请求/响应 headers + body（文本/hex）。
- 服务器真实上游 IP、CONNECT 隧道与 mock 短路标记。
- 表头排序、按方法过滤、域名黑白名单、隐藏 CONNECT/Image。
- Mock 规则：命中整行着色、MOCK 标记；支持导入 Fiddler `CustomRules.js` 的典型 mock 模式（预览/勾选）。
- WebSocket 连接与逐条消息；Socket.IO 事件格式化。
- JSONPath 轻量子集：`$.a.b`、`$['a']`、`$[0]`、`$[-1]`、`$[1:3]`、`$[*]`、`$..name`、过滤 `[?(@.price > 10 && @.x =~ 'A|B')]`、聚合 `length()/min()/max()`。
- JSON 工具/比对、网络模拟（4G/3G/2G/off）、重放并对比、会话保存/恢复、导出 cURL/原始报文/HAR 1.2、多选批量。
- 手机抓包：二维码/证书页面，iOS 需在“证书信任设置”启用。
- 快捷键、浅色/深色主题、中文界面。

使用：

1. 下载 release 或 `pip install -r requirements.txt`。
2. 启动后确认自动代理；手机与电脑同网，按提示安装 CA。
3. 在“Mock 规则”新增规则；命中后自动返回 mock。
4. 重放并对比：调整参数/响应后查看差异。
5. 保存会话，导出 HAR 供后续分析。

注意事项：流量过滤/搜索只影响显示，不影响抓取；JSONPath 不支持脚本表达式；API 调试直连目标服务器，不走抓包代理。

## 4. mitmproxy-mcp（MCP + 本机控制台）

架构：MCP 服务（stdio） → 控制服务（FastAPI，`~/.mitmscope/`） → mitmdump。支持 Android/iOS 真机与模拟器，以及 Mac 本机流量。

安装：

```bash
# 远程一键（clone 到 ~/.mitmproxy-mcp、装依赖、配置 MCP、安装 skill）
curl -fsSL https://raw.githubusercontent.com/Aillumine/mitmproxy-mcp/main/install.sh | bash
# 本地
bash install-skill.sh
```

MCP 配置（Cursor/Claude 等）：

```json
{
  "mcpServers": {
    "user-mitmproxy": {
      "command": "uv",
      "args": ["--directory", "/path/mitmproxy-mcp", "run", "mitmproxy-mcp"]
    }
  }
}
```

启动：

```bash
uv run mitmproxy-control --proxy    # 网页控制台 + 后台抓包（默认不改 Mac 系统代理）
uv run mitmproxy-control --open     # 只要网页
uv run mitmproxy-start              # 仅代理
```

MCP 工具：

| 工具                                            | 说明                     |
| --------------------------------------------- | ---------------------- |
| `proxy_start` / `proxy_stop` / `proxy_status` | 代理生命周期                 |
| `throttle_get` / `throttle_set`               | 弱网档位（off/4g/3g/2g）     |
| `traffic_list`                                | 列出流量（域名/状态码/类型筛选）      |
| `traffic_search`                              | 搜索 URL/请求头/请求体/响应头/响应体 |
| `traffic_get_detail`                          | 请求元数据                  |
| `traffic_read_body`                           | 分片读取大响应                |
| `traffic_clear`                               | 清空流量                   |
| `get_cert_info`                               | 证书安装指南                 |

数据目录：`~/.mitmscope/traffic.db`、`mock.db`、`throttle.json`、`runtime.json`、`control.log`。Web 控制台与 MCP 共用同一数据库。

### 4.1 真机抓包（推荐路径）

Android（adb reverse，免手填 Wi-Fi）：

1. `proxy_start`（不要开 Mac 系统代理）。
2. `android_list_devices` → `android_reverse_proxy(serial, 8888)`。
3. 设备全局代理变为 `127.0.0.1:8888`，经 USB 到本机 mitm。

设备 Wi-Fi 方案（无 adb/必须无线）：`android_setup_proxy(serial, MacIP, 8888)` 或手动设置 Wi-Fi 代理。

iOS 模拟器：可跟随 Mac 系统代理（仅用户明确要求 `setup_proxy=true`）；否则在模拟器 Wi-Fi 填 `127.0.0.1:8888`。

真机规则：**不要**开启 Mac 系统代理，避免污染本机网络。`setup_proxy` 在 `device` 目标下强制禁止。

### 4.2 证书

iOS 模拟器：Safari 访问 `http://mitm.it` → Apple → 安装描述文件 → 设置 → 通用 → 关于本机 → 证书信任设置 → 启用 mitmproxy。

Mac 浏览器：同样访问 `mitm.it`，安装 `mitmproxy-ca-cert.pem` 到钥匙串并“始终信任”，否则 HTTPS 打不开。

Android 7+：用户 CA 默认不被应用信任。仅在自有/授权设备上：使用可信任用户 CA 的 app 配置、debuggable app、或 root/模拟器安装系统 CA；不要绕过他人设备的证书策略。

### 4.3 WebSocket 排错

- WSS 在 Socket 分类，不在 HTTP。
- 只有心跳 `2`/`3`、没有 `0{sid}`：旧版本可能破坏 `permessage-deflate`；当前 addon 会移除该扩展，重启代理再连。
- TLS `certificate unknown`：Android 未信任 CA；不是过滤问题。
- 重启代理不会清库；清空要用页面 Clear。

## 5. 抓包后的证据组织

建议目录：

```
case/
├── capture/
│   ├── flows.jsonl
│   ├── requests/           # 导出的原始请求
│   └── cert-notes.md
├── notes/
│   ├── chain.md            # 请求链：触发→前置→目标→后续
│   └── hypotheses.md       # 事实/推断分开
└── result/
```

请求链记录最少包含：序号、时间、方法、URL、状态、请求头（脱敏）、请求体摘要、响应摘要、触发动作、上游依赖、结论。对关键请求保存原始 bytes/hash，避免只留截图。

## 6. 移动端 HTTPS 与固定证书

1. 先在授权设备上安装 CA（见上）。
2. 观察目标是否固定证书：请求失败但浏览器正常，常见于 pinning/双向 TLS。
3. 在 App 上分析 pinning：Frida hook 证书校验、network security config（debug 构建）、或服务端测试环境。第三方生产 App 绕过安全控制。
4. 抓不到时不要臆测“没有请求”：检查 QUIC、代理绕过、VPN、私有 DNS、证书失败。
5. 对加密 payload，先记录完整请求/响应，再在 JS/App 侧定位加解密函数（见 JS/移动参考）。
