# 浏览器指纹与反检测环境

覆盖来源：`Virtual-Browser/VirtualBrowser`、`musiclover789/luna`、`zhaotoday/fingerprint-browser`、`hisune/antidetect-browser`、`LoseNine/Firefox-FingerPrint-Analyzer`（RuyiTrace，原仓库已删除）、`TideSec/TideFinger_Go`。

## 1. 指纹面（理解检测对象）

| 类别        | 典型字段                                                                         |
| --------- | ---------------------------------------------------------------------------- |
| 网络        | IP、ASN、时区、语言、DNS、WebRTC 本地/公网 IP、代理类型                                        |
| Navigator | UA、platform、vendor、languages、hardwareConcurrency、deviceMemory、webdriver      |
| 屏幕/窗口     | width/height、availWidth/Height、colorDepth、devicePixelRatio、ClientRects       |
| 图形        | Canvas 2D 噪声、WebGL/WebGPU vendor/renderer/extensions/parameters、AudioContext |
| 字体/语音     | 字体列表、SpeechSynthesis voices                                                  |
| 媒体/硬件     | 媒体设备枚举、电池、触控点、CPU/内存                                                         |
| 存储/Cookie | Cookie、localStorage、IndexedDB、缓存、分区状态                                        |
| 行为        | 鼠标轨迹、键盘节奏、点击/滚动、isTrusted                                                    |
| 协议        | TLS/JA3/JA4、HTTP/2 设置、Client Hints、Accept-Language                           |

检测站（自测基线）：

- https://browserscan.net/
- https://whoer.net/
- https://browserleaks.com/
- https://pixelscan.net/
- https://abrahamjuliot.github.io/creepjs/
- https://amiunique.org/
- https://fingerprintjs.github.io/fingerprintjs/

## 2. VirtualBrowser（开源 Chromium 指纹浏览器）

特性：

- Windows/macOS/Linux，多环境隔离（独立 profile、Cookie、缓存）。
- 指纹项：UA、代理、语言、时区、WebRTC、地理位置、分辨率、字体、Canvas/WebGL 噪声、WebGL 元数据、AudioContext、ClientRects、Speech Voices、CPU/内存、设备名/MAC、DNT、SSL/端口扫描保护、硬件加速。
- 支持按 IP 自动匹配语言/时区/地理位置。
- 基于 Chromium，可用 Playwright 或其他 Chromium 自动化工具（见仓库 `automation/`）。

使用：

1. 从 Releases 或官网下载安装。
2. 新建环境，配置代理、语言、时区、分辨率、Canvas/WebGL 等。
3. 启动环境，得到独立指纹实例。
4. 自动化：用 Playwright 连接该环境的 Chromium；或使用 CDP endpoint 接入 `js-reverse-mcp --browserUrl`。

验证：同一环境重复访问检测站，核心字段应稳定；不同环境之间应隔离。不要只用单一检测站判断“过检测”。

## 3. Luna（Go 自动化 + 抗指纹浏览器）

定位：基于视觉的抗指纹爬虫/自动化库，Windows x86-64；需要配套 Luna 浏览器才能让框架设置的指纹生效。

```bash
go get -u github.com/musiclover789/luna
```

最小示例：

```go
package main

import (
    "fmt"
    "github.com/musiclover789/luna/devtools"
)

func main() {
    _, browser := devtools.NewBrowser(`C:\path\to\luna\chrome.exe`, &devtools.BrowserOptions{
        Headless: false,
    })
    browser.OpenPage("https://example.com")
    fmt.Println("running")
    select {}
}
```

高级用法见 `luna-browser` 文档与 `test_case`：

- 缓存目录、代理、窗口尺寸、等待页面/选择器。
- 支持指纹项：UA、Canvas、WebGL/WebGPU、platform、timezone、languages、userAgentData、deviceMemory、hardwareConcurrency、WebRTC IP、screen、字体、声卡、触控、电池、ClientRects、webdriver、CDP 检测等。
- 拟人鼠标轨迹、键盘拼音输入法模拟、真实键鼠标志。

注意：部分指纹需要作者授权；只使用你合法获得的授权文件。Luna 仅 Windows x86-64，其他平台需实测。

## 4. Firefox 系指纹环境

- **RuyiPage**：Python Firefox 自动化（WebDriver BiDi，非 CDP）；支持定制 Firefox runtime、网络抓包、Cookie、拟人动作。
- **RuyiTrace**：C++ 引擎层 DOM/JS API trace，生成 NDJSON；适合高保真补环境和指纹基线（原仓库已删除，文档/脚本保留在 `erma0/js-reverse-skill`）。
- **Firefox-Reverse**：内置 AI Agent 的 Firefox 工作站，支持指纹环境管理（独立 profile/进程/Marionette 端口）、环境导入/导出、C++ 配置层指纹字段。

一致性流程：

1. 固定 profile、出口 IP、语言、时区、UA、视口。
2. 首次成功后写 `fingerprint-baseline.json`（字段值 + 来源 + `baselineId`）。
3. 后续采集/调试复用同一 baseline；更换代理/地区/工具时生成新 baseline，不混用样本。
4. 任何指纹值必须有真实浏览器证据；不要用 AI 猜值或静态推断。

RuyiPage 启动硬约束（来自 `erma0/js-reverse-skill`）：

- 必须使用已验证的 ruyiPage 定制 Firefox runtime，不能用系统 Firefox fallback。
- 有头模式、独立 profile、`smart_fingerprint` 并 `apply_emulation`。
- `page.capture.start(...)` 在 `page.get(...)` 之前；导航后检查 `navigator.webdriver === false`。
- 需要真实交互时优先原生 BiDi 动作；构造事件仅在必要时标注。
- 目标接口要捕获到非 OPTIONS 的 2xx 响应才算取证成功。

## 5. 开源指纹浏览器/内核/框架地图

来自 `zhaotoday/fingerprint-browser`（完整列表见仓库）：

**成品浏览器**：CloakBrowser、Camoufox、bb-browser、VirtualBrowser、BotBrowser、Ant-Browser、GeekezBrowser、undetectable-fingerprint-browser、YSbrowser、camofox-browser、XChrome、firefox-fingerprintBrowser、kameleo、ruyiBrowser、luna-browser、Open-Anti-Browser、FingerPrintJSBrowser、Fingerprint-Browser、social-browser、OpenBrowser。

**内核源码级定制**：fingerprint-chromium、Chrome Power、Venom-aoman、openFpchromium、chromium_fingerprint。

**轻量/嵌入式内核**：ladybird、Lightpanda、miniblink49、CEF、mini_chromium、miniblink132。

**自动化/反检测框架**：Stagehand、Automa、SeleniumBase、undetected-chromedriver、steel-browser、pydoll、nodriver、chrome-remote-interface、invisible_playwright、patchright-nodejs、AutoWK、cyCronet、chromium-bidi、undetected-browser、antidetect、botbrowser-mcp。

**指纹注入系列**：puppeteer-with-fingerprints、playwright-with-fingerprints、browser-with-fingerprints、selenium-with-fingerprints。

**指纹生成/数据集**：fingerprint-suite（Apify）、browserforge、user-agents、simprint、chrome-fingerprints、fingerprint-generator。

**检测/分析**：FingerprintJS、creepjs、browser、fpscanner、trustdevice-js、Firefox-FingerPrint-Analyzer（RuyiTrace）、DeviceJs、get-browser-fingerprint、browser-fingerprint、digital-fingerprint。

**多开/管理**：donutbrowser、Chrome Power App、Chrome-Manager、ChromiumManager、by-chrome-app、Browser-Manager、camoufox-profile-manager。

**远程/云浏览器**：neko、BrowserBox。

**取证/调试**：HackBrowserData、hindsight、debugger-protocol-viewer、AI_JS_DEBUGGER、chromium-ipc-sniffer。

**教程/资源**：HeadlessBrowsers、browser-fingerprinting、Chromium_FingerPrint_Tutorial、awesome-anti-detect、Top-antidetect-browser、AntidetectBrowser。

**代理/IP**：MyIP、ip-info-api、zhuzhai-ip、socks5-proxy、ispip；代理服务商对比见资源仓库的 28 家列表。

## 6. 商业指纹浏览器与代理选型

来自 `hisune/antidetect-browser`：

| 产品           | 免费环境 | 备注                   |
| ------------ | ----:| -------------------- |
| AdsPower     | 2    | 老牌，窗口同步/RPA/API/团队协作 |
| FlashID      | 内测   | UI 简洁，云手机            |
| GoLogin      | 3    | 内置代理                 |
| Dolphin Anty | 5    | 无中文                  |
| 比特浏览器        | 10   | 功能类似 AdsPower，UI 较杂  |
| GenLogin     | 5    | UI 复古                |
| Multilogin   | 无    | 基础                   |
| Kameleo      | 无    | 基础                   |
| Vision       | 无    | UI 好看                |

代理选型要点（来自 `zhaotoday/fingerprint-browser`）：住宅/ISP 代理优先，移动代理成本高；确认国家/城市、粘性会话、并发、计费、IP 纯净度；代理出口需与语言/时区/地理一致。不要在报告中记录代理账号密码。

## 7. TideFinger_Go（Web/主机指纹识别）

定位：Go 版指纹识别工具，整合 2.3 万+ Web/主机指纹，支持多 URL、IP、CIDR；并发高。参考 fscan/Dismap/Vscan/Kscan/ServerScan 等。

```bash
TideFinger -h 192.0.0.1/24 -p 80 -np -nobr -nopoc
TideFinger -uf url.txt -nobr -nopoc -pt 120
TideFinger -u http://www.example.com -pd
```

- `-nobr` 关闭口令暴力破解；`-nopoc` 关闭 POC 检测；`-pd` 显示 POC 详情。
- 默认构建开启了口令破解/POC，扫描第三方资产可能违法或造成损害；只在你拥有或明确获授权的资产上使用，并优先 `-nobr -nopoc`。
- 结果用于资产梳理/指纹识别，不要用于未授权入侵。

## 8. 自动化与调试接入

- **Playwright + 指纹浏览器**：多数产品提供 Chromium/CDP；启动后拿 `http://127.0.0.1:<port>`，用 `js-reverse-mcp --browserUrl` 或 `chrome-remote-interface` 接入。
- **CDP endpoint 注意**：厂商私有 Local API 不是 CDP；必须能响应 `/json/version`。
- **代理**：指纹环境与抓包代理可同时使用；注意代理链（浏览器→mitmproxy→上游代理）与 DNS 泄漏。
- **验证**：分别在目标站和检测站验证；记录 baseline，不频繁随机化（随机化本身可能成为异常信号）。
- **行为**：真实键鼠/点击优先；程序化事件与固定轨迹容易被行为检测识别。只在授权测试中使用拟人化能力。

# 
