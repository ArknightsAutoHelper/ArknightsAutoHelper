# 一份简单的OCR模块安装文档

> 由于在后续的版本中将要逐渐废弃不支持OCR模块的功能。所以这里放一个简单的OCR模块安装教程
> 目前大家主流使用的是 tesseract V4.x 的版本不推荐使用 3.x 的版本应为在中文的识别上有些过拟合

## tesseract 官方页面

https://github.com/tesseract-ocr/tesseract

## Windows 版本的下载链接

- tesseract-ocr-w64-setup-v4.1.0-bibtag19.exe,
    - https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v4.1.0-bibtag19.exe
- tesseract-ocr-w64-setup-v4.1.0-elag2019.exe,
    - https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v4.1.0-elag2019.exe
    
安装完毕后请确认系统变量已经安装，并在安装时候勾选中文语言支持

如果你没有添加中文语言支持。可以下载中文的训练向量包并把它放到对应路径下

#### 语料包的下载地址

- https://github.com/tesseract-ocr/tessdata/raw/4.00/chi_sim.traineddata

#### 语料包的安装文档

- https://github.com/tesseract-ocr/tesseract/wiki/Data-Files

## 测试

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
