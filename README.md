# Arknights Auto Helper GUI版本
> 明日方舟辅助脚本，分支说明如下

| 分支    | 说明    |
|:----|:----|
| master |目前的稳定版本|
|release |目前可以应用的GUI版本|
| dev |目前的开发版本|
| shaobao_adb |经过封装可以移植的ADB方法类|

## GUI 下载地址

- 百度 网盘
    - 链接：https://pan.baidu.com/s/1N5EBCVhdW6XkQdVFcSKa1g  提取码：l4nd 
    - 版本为 8.31提交的版本
    
    
## 启动

可以下载打包过的 exe 文件后快速启动，由于pyinstaller打包比较坑，现在必然会弹出那个可爱的命令行。

![TIM图片20190612102050.png-48.6kB][2]

在启动前请点击初始化辅助，这样会加载相关配置信息。


## 设置

设置采用json格式的文件，相关配置在 settings.json 下。关于配置详情请查看主分支下的README.md
在此只做简略介绍。

由于作者精力有限，暂时不打算做这个GUI，所以请自己修改配置文件。以下为事例文件

```json
{
  "ADB_HOST": "127.0.0.1:60001",
  "enable_adb_host_auto_detect": true,
  "enable_ocr_check_update": true,
  "enable_ocr_check_end": true,
  "enable_ocr_check_task": true,
  "enable_ocr_debugger": true,
  "enable_ocr_check_is_TASK_page": true,
  "enable_rebase_to_null": true,
  "enable_baidu_api": false,
  "enable_help_baidu": true,
  "APP_ID": " App ID",
  "API_KEY": " Api Key",
  "SECRET_KEY": " Secret Key",
  "DEBUG_LEVEL": 2,
  "ArkNights_PACKAGE_NAME": "com.hypergryph.arknights",
  "ArkNights_ACTIVITY_NAME": "com.u8.sdk.U8UnityContext"
}
```

- ADB_HOST ： ADB 的端口，如果你不想用多开功能可以留空字符串，一般夜神模拟器的第一个设备端口为 `127.0.0.1:60001`

**OCR 高级设置**
> 以下设置如果要开启请启用百度API或者安装本地OCR识别环境和中文依赖包。
关于OCR的安装文档可以看主分支下的OCR_install.md

- enable_ocr_check_update ： 升级的时候是否用OCR检测，默认为子图识别
- enable_ocr_check_end ： 战斗结束的时候是否用OCR检测，默认为子图识别
- enable_ocr_check_task : 启动ocr来检测任务是否已完成
- enable_ocr_debugger ： 出错的时候是否用OCR检测，出错检测为两处。不小心点到设置界面和不小心点到素材界面，默认为子图识别
- enable_ocr_check_is_TASK_page : 启用ocr来检测是否在关卡界面
- enable_rebase_to_null : 关闭大量的OCR命令输出，推荐设置为 ture 也就是关闭
- enable_api : 是否启用 百度 API
    - APP_ID;API_KEY;SECRET_KEY
    - 百度API的参数
- enable_help_baidu : 是否对使用百度ocr的图像进行处理，有可能改善精准度，但也有可能反而导致识别错误；该选项不会影响tesseract
- DEBUG_LEVEL : 0 为不输出 1 为输出函数调用 2 为输出全部调试信息 【GUI版本输出关系不大】
- ArkNights_PACKAGE_NAME ： 明日方舟启动的程序名，如果你是b服请改为 com.hypergryph.arknights.bilibili

## 自己编译

如果不方便下载 完整的文件，那么可以自行编译，需要安装 pyinstaller 并输入如下命令
```bash
$ pyinstaller -F GUI_start.py
$ mv dist/GUI_start.exe ./
```
我已经将该命令写在 make_GUI_start_exe.bat 中，有需要可自行执行。

  [2]: http://static.zybuluo.com/shaobaobaoer/860t36w2ygsvet6sxn3lv3ty/TIM%E5%9B%BE%E7%89%8720190612102050.png