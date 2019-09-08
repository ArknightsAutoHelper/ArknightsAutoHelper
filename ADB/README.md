## ADB 目录
### 说明

旨在提供adb的可执行程序从根本上解决手动配置路径的问题。
后期可能会让项目文件过大。考虑会采用额外配置包的形式

### 相关ADB的下载地址

TODO

### 各个机型的返回值(文件夹名字)
> 参考 https://stackoverflow.com/questions/446209/possible-values-from-sys-platform

```text
┍━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━┑
│ System              │ Value               │
┝━━━━━━━━━━━━━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━━━┥
│ Linux               │ linux or linux2 (*) │
│ Windows             │ win32               │
│ Windows/Cygwin      │ cygwin              │
│ Windows/MSYS2       │ msys                │
│ Mac OS X            │ darwin              │

(*) Prior to Python 3.3, the value for any Linux version is always linux2; after, it is linux.
```
