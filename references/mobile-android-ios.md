# Android / iOS 逆向

覆盖来源：`langgithub/RxAppEncryptionProtocol`、`WuFengXue/android-reverse`、`DamonZS/PE-reverse-skill`（Android 能力）、`weixinbao/ReverseTool`（iOS/Android 工具索引）、`Aillumine/mitmproxy-mcp`（真机抓包）。

> 

## 1. Android 工具链

| 类别     | 工具                                                      | 用途                |
| ------ | ------------------------------------------------------- | ----------------- |
| 设备     | adb、scrcpy                                              | 安装/日志/文件/屏幕       |
| 反编译    | jadx/jadx-gui、GDA、JEB（商业）、BytecodeViewer、APK Analyzer   | DEX→Java          |
| 资源/重打包 | apktool、AXMLPrinter、Apk Easy Tool                       | 解包/回编译            |
| DEX    | dex2jar、enjarify、baksmali/smali、Simplify                | 转换/反混淆            |
| 动态     | Frida、Xposed/LSPosed、objection、Cydia Substrate、ADBI/DDI | Hook/插桩           |
| Native | IDA、Ghidra、radare2、Binary Ninja、SoFixer、unicorn、unidbg  | .so 分析/模拟执行       |
| 脱壳     | FDex2、FART、定制 ART 镜像                                    | 运行时 dump DEX      |
| 抓包     | mitmproxy/mitmproxy-mcp、Charles、Frida                   | HTTP(S)/WebSocket |

`WuFengXue/android-reverse` 是上述工具的中文索引，含每条工具的原理与适用版本；`weixinbao/ReverseTool` 补充 Java/Android/iOS/.NET 工具。

## 2. APK 静态分析

```bash
# 基础信息
aapt dump badging app.apk | head
unzip -l app.apk | head -40
apksigner verify --print-certs app.apk

# 反编译 Java
jadx -d out_jadx app.apk
jadx-gui app.apk

# 资源 + smali
apktool d app.apk -o out_apktool

# DEX → JAR（可选）
d2j-dex2jar app.apk -o app.jar
```

检查清单：

- `AndroidManifest.xml`：包名、权限、exported 组件、networkSecurityConfig、debuggable、备份开关。
- `lib/<abi>/*.so`：native 逻辑、加壳/混淆、JNI 注册。
- `assets/`：模型、配置、加密数据、WASM/JS。
- 证书/签名：是否重打包检测、签名校验。
- 加固特征：DEX 头异常、多个 Dex、类加载器、`libjiagu`/`libshell` 等。
- 反调试：`ptrace`、`/proc/self/status`、Frida 端口/线程扫描、Xposed 检测。

## 3. 动态分析（Frida）

```bash
pip install frida-tools objection
adb shell getprop ro.product.cpu.abi
frida-ps -U
frida -U -f com.example.app -l hook.js --no-pause
frida -U -n com.example.app -l hook.js
```

### 3.1 RxAppEncryptionProtocol（Java 加密协议）

来源：`langgithub/RxAppEncryptionProtocol`。思路：Hook Java/JDK 的加密函数，打印入参/返回值，还原协议。

```bash
frida -U -l js_hook.js -f com.lang.testso --no-pause
```

脚本覆盖：

- MD5、AES、DES、RSA 等常见加密 API。
- SSL Pinning 处理（用于授权抓包）。
- 点击发送请求后，在 Frida 日志查看明文/密文/密钥/IV。
- 将打印的十六进制转 byte 数组，在本地重建加密现场（`com.lang.script` 测试代码）。
- native 动态注册函数打印（JNI `RegisterNatives`）。

注意：随仓库的 `js_hook.js` 可能针对旧版 Android/Frida；先在小样本验证，按当前类名/方法签名调整。

### 3.2 常用 Hook 模板

```javascript
// 打印 Java 方法调用
Java.perform(() => {
  const Cipher = Java.use('javax.crypto.Cipher');
  const doFinal = Cipher.doFinal.overload('[B');
  doFinal.implementation = function (input) {
    console.log('[Cipher.doFinal] in=', Java.array('byte', input));
    const out = doFinal.call(this, input);
    console.log('[Cipher.doFinal] out=', Java.array('byte', out));
    return out;
  };
});

// 枚举类加载器/类
Java.enumerateLoadedClasses({
  onMatch(name) { if (name.includes('sign')) console.log(name); },
  onComplete() {}
});

// Native 导出/注册
const lib = Module.load('libnative.so');
lib.enumerateExports().filter(e => e.name.includes('sign')).forEach(console.log);
```

### 3.3 SSL Pinning（授权环境）

- 先确认失败原因（证书固定、双向 TLS、QUIC、代理绕过）。
- 在自有/授权测试 App 上，可用 Frida hook `TrustManager`、`SSLContext`、OkHttp `CertificatePinner`、Conscrypt 等。
- 不要把绕过脚本用于第三方生产 App；不要绕过金融/支付安全控制。

## 4. 抓包（Android）

推荐 mitmproxy-mcp（见 `network-capture.md`）：

```bash
# 1) 启动代理（不设置宿主系统代理）
# 2) adb reverse
adb reverse tcp:8888 tcp:8888
adb shell settings put global http_proxy 127.0.0.1:8888
# 或通过 mitmproxy-mcp: android_list_devices → android_reverse_proxy(serial, 8888)
```

- 安装 CA：`http://mitm.it`（浏览器/设置）；Android 7+ 用户 CA 默认不被 App 信任。
- 对自有 App：debuggable + network security config 信任用户 CA；或 root/模拟器安装系统 CA。
- 对授权测试：按合约处理 pinning；记录操作与范围。
- 清除代理：`adb shell settings put global http_proxy :0`，并移除 CA。

## 5. 脱壳与 Native

- **FDex2**：Xposed 模块，Hook `ClassLoader.loadClass`，反射取 `Dex` 并写出；适用于 Android 4.4+ 旧环境。
- **FART**：ART 自动化脱壳，支持 6.0–8.0，需刷机/镜像。
- **SoFixer**：修复内存 dump 的 .so section。
- **unicorn/unidbg**：模拟执行 ARM32/ARM64（及实验性 iOS）native 函数，适合黑盒调用 `sign`/加密函数。
- **Ghidra/IDA/radare2**：静态分析 .so；JNI 动态注册需找 `RegisterNatives` 表恢复函数名。
- **JNI 要点**：`Java_<pkg>_<Class>_<method>` 静态注册；动态注册通过 `RegisterNatives(JNIEnv*, jclass, JNINativeMethod*, int)`，在 `JNI_OnLoad` 中调用；Hook 它可打印函数名/签名/地址。

加固/反调试是分析障碍：先识别厂商（DIE/字符串/so 名）、记录证据；在授权环境中可选择脱壳/插桩；不要绕过第三方保护用于侵权。

## 6. PE-reverse-skill 的 Android 能力

```bash
# 完整 APK 静态分析
python -m reverse_analyzer android analyze .\app.apk --out .\android-analysis

# 受边界保护的解包（默认 ZIP，10k 成员/128MiB 单文件/768MiB 总量/压缩比 1000）
python -m reverse_analyzer android unpack .\app.apk --out .\android-unpack --destination .\decoded

# 验证后逐字节复制（不是反编译重建）
python -m reverse_analyzer android rebuild .\app.apk --out .\android-rebuild --apk-out .\rebuilt.apk --strategy zip_copy
python -m reverse_analyzer android verify .\rebuilt.apk --out .\android-verify

# apktool + apksigner 重建（需要签名配置）
python -m reverse_analyzer android rebuild .\app.apk --out .\android-rebuild --project-dir .\decoded --apk-out .\rebuilt-signed.apk --strategy apktool_rebuild --apktool C:\Tools\apktool.bat --apksigner C:\Android\build-tools\35.0.0\apksigner.bat --keystore C:\Keys\research.jks --key-alias research
python -m reverse_analyzer android verify .\rebuilt-signed.apk --out .\android-verify --apksigner C:\Android\build-tools\35.0.0\apksigner.bat --param verify_signature=true
```

- `zip_copy` 输出哈希应与源 APK 相同；它不是“反编译后重构”。
- 缺少 apktool/apksigner/签名配置时返回 `unavailable`。
- 只在授权 App 上重打包；签名密钥妥善保管。

## 7. iOS 工具与流程

工具索引（ReverseTool）：

- 反汇编/反编译：IDA Pro、Hopper、Ghidra。
- UI/运行时：Reveal、PonyDebugger、Cycript、LLDB、snoop-it、Introspy。
- 文件/设备：iFunbox、iExplorer、iTools。
- 网络：Charles、mitmproxy。
- Hook/开发：Theos、iOSOpenDev、Frida、objection。
- 符号：class-dump。

流程：

1. 获取 IPA（自有/授权）→ 解压 → `Payload/App.app`。
2. 静态：`file`、`otool -l/-L`（mach-o）、class-dump（Objective-C 头）、Ghidra/IDA 分析二进制、strings、plist、资源。
3. 动态：越狱设备/模拟器 + Frida/objection；LLDB；Cycript（旧）。
4. 网络：mitmproxy/Charles，安装 CA 并在“证书信任设置”启用；pinning 在授权环境处理。
5. Swift/Objective-C 符号恢复：Swift demangle、`nm`、class-dump；strip 后依赖运行时/字符串/交叉引用。
6. 重打包/签名：仅在自有/授权 App 上；需要开发者证书/描述文件；不要分发修改后的第三方 App。

PE-reverse-skill 的 `analyze`/`source reconstruct` 支持 IPA/app 的静态证据与 GUI 识别（UIKit/SwiftUI/Flutter/React Native/Unity），但不等于完整源码恢复。

## 8. 设备/环境操作

```bash
adb devices
adb shell pm list packages | grep -i target
adb shell dumpsys package com.example.app | head -40
adb logcat -c && adb logcat | grep -i -E 'frida|crypto|sign|exception'
adb pull /sdcard/Download/out.txt
adb shell am start -n com.example.app/.MainActivity
```

- 使用测试设备/模拟器；开启快照；不要在个人主设备安装来源不明的 Frida server/模块。
- 记录 Android 版本、ABI、Frida 版本、App 版本/签名；这些会影响脚本兼容性。
- 对 App 的反调试/完整性校验，先记录触发点，再决定是否在授权范围内绕过。

## 9. 交付检查清单

- [ ] 授权范围、设备、App 版本、哈希
- [ ] 静态证据（manifest、DEX、so、资源、加固）与动态证据分离
- [ ] Hook 脚本版本、注入点、日志样本可复现
- [ ] 网络抓包成功条件（CA、代理、pinning）说明；未授权不绕过
- [ ] 算法还原有输入/输出样本，至少多次请求验证
- [ ] 重打包/签名仅限授权 App，密钥与凭据脱敏
- [ ] 报告不包含用户隐私数据、token、密钥
