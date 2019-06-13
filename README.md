# Arknights Auto Helper GUI版本

## 启动

可以下载打包过的 exe 文件后快速启动，由于pyinstaller打包比较坑，现在必然会弹出那个可爱的命令行。

![TIM图片20190612102050.png-48.6kB][2]

在启动前请点击初始化辅助，这样会加载相关配置信息。

## 设置

设置采用json格式的文件，相关配置在 settings.json 下。关于配置详情请查看主分支下的README.md
在此只做简略介绍。

由于作者精力有限，暂时不打算做这个GUI，所以请自己修改配置文件

```json
  "ADB_ROOT": "D:\\Program Files\\Nox\\bin", 
  "ADB_HOST": "",
  "enable_ocr_check_update": true,
  "enable_ocr_check_end": true,
  "enable_ocr_debugger": true,
  "enable_rebase_to_null": true,
  "enable_api": false,
  "APP_ID": "",
  "API_KEY": "",
  "SECRET_KEY": "",
  "ArkNights_PACKAGE_NAME": "com.hypergryph.arknights",
  "ArkNights_ACTIVITY_NAME": "com.u8.sdk.U8UnityContext"
```

- ADB_ROOT ： ⚠ 这个配置必须更改，为你模拟器的根路径，不要在最后加 “ \\ ”
- ADB_HOST ： ADB 的端口，如果你不想用多开功能可以留空字符串，一般夜神模拟器的第一个设备端口为 `127.0.0.1:60001`

**OCR 高级设置**
> 以下设置如果要开启请启用百度API或者安装本地OCR识别环境和中文依赖包。
关于OCR的安装文档可以看主分支下的OCR_install.md

- enable_ocr_check_update ： 升级的时候是否用OCR检测，默认为子图识别
- enable_ocr_check_end ： 战斗结束的时候是否用OCR检测，默认为子图识别
- enable_ocr_debugger ： 出错的时候是否用OCR检测，出错检测为两处。不小心点到设置界面和不小心点到素材界面，默认为子图识别
- enable_rebase_to_null : 关闭大量的OCR命令输出，推荐设置为 ture 也就是关闭
- enable_api : 是否启用 百度 API
    - APP_ID;API_KEY;SECRET_KEY
    - 百度API的参数
- ArkNights_PACKAGE_NAME ： 明日方舟启动的程序名，如果你是b服请改为 com.hypergryph.arknights.bilibili

  [2]: http://static.zybuluo.com/shaobaobaoer/860t36w2ygsvet6sxn3lv3ty/TIM%E5%9B%BE%E7%89%8720190612102050.png