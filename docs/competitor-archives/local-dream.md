# local-dream — Android 端侧 Stable Diffusion

> 存档 2026-06-18 · 对照 shadow-verse · ⚪以后可能用(本地/离线出图后端范本)

## 定位
跑在 Android 手机上、用骁龙 NPU(Hexagon)加速本地出图的开源 Stable Diffusion app,纯端侧、可离线、免费。

## 技术栈 / 规模
Kotlin+Jetpack Compose(UI/服务/数据)+C++17 推理核(编译为 `libstable_diffusion_core.so`)。双后端:QNN(Qualcomm NPU/Hexagon V68-V81)+MNN(CPU/GPU/OpenCL)。第三方:cpp-httplib/nlohmann-json/xtensor/mlc tokenizers/stb/zstd。C++ 推理核 ~30 hpp+main.cpp 751 行;Kotlin ~60 文件。

## 核心机制剖析(本地端侧出图)

**1. 本地 HTTP 后端进程模型**(架构亮点):C++ 推理核编译成 .so,**当可执行文件用 ProcessBuilder 起本地 HTTP 服务**(默认 127.0.0.1:8081)。`BackendService.kt`(Android 前台 Service)负责拷 QNN .so 设可执行位、组命令行、设 LD_LIBRARY_PATH/DSP_LIBRARY_PATH、起进程、单线程串行、监控 stdout、收尾。Kotlin UI 通过 OkHttp 调本地 HTTP。端点:`POST /generate`(**SSE 流式**逐 step 进度+预览图,客户端断连即中止省电)/`POST /upscale`/`POST /tokenize`/`GET /health`。`g_generation_mutex` 串行化(共享 MNN session 不能并发)。

**2. prompt tag 自动补全**(`TagAutocompleteRepository.kt`):成熟的 Danbooru 风 tag 补全:CSV 词典(english/category/postCount/aliases)+翻译 CSV(中文→英文 tag);**CharBitmap 位图预过滤**+子序列模糊匹配+有界 top-K 堆+Damerau-Levenshtein 编辑距离纠错+postCount 人气加权;二进制缓存。含 A1111 注意力权重语法(`(tag)`=1.1/`[tag]`=0.9/`(tag:n)`)和 embedding 逐字匹配。

**3. ParamShare 参数可复现**(`ParamShare.kt`):把生成参数(prompt/negative/steps/cfg/seed/scheduler/denoise/mode+model_id)打包成带 `_localdream_params` 标识键的 JSON,可 base64+`LDPARAMS:` 前缀贴剪贴板,tryDecode 识别裸 JSON 或带前缀两种,schema 带版本号。

**4. RequestParser.hpp 出图参数全集**:prompt/negative/steps/cfg/scheduler/seed/width/height/denoise/preview_format;img2img/inpaint(base64 image+mask);ultrafix(分块 tiled img2img 到 8192px);SDXL aspect_ratio(合成 inpaint padding)。

## 借鉴清单

| # | 借鉴点 | 对应能力 | 状态 | 移植 | 优先级 |
|---|---|---|---|---|---|
| 1 | 本地推理核当 HTTP 子进程+SSE 流式进度 | 本地出图后端(未来) | ⚪以后可能用 | 仅思路(C++/Android,shadow-verse 是 Python) | 低 |
| 2 | prompt tag 自动补全/翻译/权重语法 | render prompt 规范化 | 🔵仍可借 | 仅思路(算法可重写 Python) | 中 |
| 3 | ParamShare 出图参数复现 schema | render 参数分享/复现 | 🔵仍可借 | 直接移植 schema 设计 | 中 |
| 4 | A1111 注意力权重语法解析 | prompt 编辑 | ⚪以后可能用 | 仅思路 | 低 |

## 不值得碰
整个 C++ QNN/MNN 推理核、Hexagon 多架构 .so、SDXL lowram、ultrafix tiling、VAE 编解码、Compose UI、Android Service:硬件端侧专属,与 shadow-verse 云出图(Gitee)正交。

## 存档备忘(以后可能用)
- **若 shadow-verse 将来要做「本地/离线出图」**:`BackendService.kt`+`main.cpp` 这套「推理核子进程+本地 HTTP+SSE 逐 step 进度+客户端断连即中止」是最值得照搬的整体架构(用 Python 重写后端,协议照搬)。
- TagAutocompleteRepository 的位图预过滤+模糊+人气加权+翻译映射,是做中文友好 prompt 输入的高质量参考。
- ParamShare 标识键+版本号+base64 剪贴板编码可直接用于出图参数分享。
