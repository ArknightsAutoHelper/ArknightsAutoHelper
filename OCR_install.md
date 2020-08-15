# OCR 安装说明

## OCR 后端比较

后端                          |识别速度          |准确率
------------------------------|------------------|------
[Tesseract](#Tesseract)        |慢                |高
[Windows OCR](#windows-ocr)   |快                |中
[百度 OCR API](#百度-ocr-api) |快，但有 QPS 限制 |高


## Tesseract

安装说明：https://tesseract-ocr.github.io/tessdoc/Home.html

### TL;DR; for Windows

参考 https://github.com/UB-Mannheim/tesseract/wiki

- tesseract-ocr-w32-setup-v5.0.0-alpha.20200328.exe (x86),
    - https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w32-setup-v5.0.0-alpha.20200328.exe
- tesseract-ocr-w64-setup-v5.0.0-alpha.20200328.exe (amd64),
    - https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v5.0.0-alpha.20200328.exe
    
安装需要勾选中文语言支持，安装完毕后请将安装路径加入 PATH 环境变量。

如果你没有添加中文语言支持。可以下载中文的训练向量包并把它放到对应路径下

#### 语料包的下载地址及安装文档

https://tesseract-ocr.github.io/tessdoc/Data-Files

### 测试

#### 版本
```bash
$ (venv) D:\python_box\shaobao_adb>tesseract -v
tesseract v4.1.0-bibtag19
 leptonica-1.78.0
  libgif 5.1.4 : libjpeg 8d (libjpeg-turbo 1.5.3) : libpng 1.6.34 : libtiff 4.0.9 : zlib 1.2.11 : libwebp 0.6.1 : libopenjp2 2.2.0
 Found AVX2
 Found AVX
 Found SSE
```

#### 支持语言
> 请确认 chi_sim 模块已经安装

```bash
$ (venv) D:\python_box\shaobao_adb>tesseract --list-langs
List of available languages (8):
chi_sim
chi_tra
eng
```

## Windows OCR

需要 Windows 10。

Windows 的 OCR 语言支持一般随该语言的基本语言支持（键盘/输入法）一同安装，部分版本的 Windows 10 可以在可选功能中手动安装。

可以通过检查 `C:\Windows\OCR` 确认语言支持是否安装。

当前默认配置为在 tesseract 无法使用（未安装）时使用。如要强制使用，请在 `config.yaml` 中配置
```yaml
ocr:
  engine: windows_media_ocr
```

## 百度 OCR API

> 百度普通的文字识别免费为50000次/日，可以开通付费，超过免费调用量后，根据百度文字识别文档，会暂停使用，建议使用前阅读文档，不保证政策是否改变。

文档地址：https://cloud.baidu.com/doc/OCR/index.html
理论上每天次数非常充足。

启用百度api作为ocr识别方案，需要自行注册百度云。并在 `config.yaml` 中配置
```yaml
ocr:
  engine: baidu
  # 百度 API 设置，使用 baidu OCR 时需要正确填写
  baidu_api:
    # 是否将百度 OCR 标记为可用
    enabled: true
    # 百度 API 鉴权数据
    app_id: '你的 App ID'
    app_key: '你的 Api Key'
    app_secret: '你的 Secret Key'
```
