from .schemadef import *

class ControllerConfig(Schema):
    screenshot_method = EnumField(['aah-agent', 'aosp-screencap'], 'aah-agent', '截图方式', 'aah-agent：截图速度更快，且支持 wm size 动态调整分辨率，但部分模拟器不兼容（截图黑屏或卡死）\naosp-screencap：使用 AOSP screencap 命令，速度较慢，但兼容性好。')
    input_method = EnumField(['aah-agent', 'aosp-input'], 'aah-agent', '输入注入方式', 'aah-agent：使用 aah-agent；\naosp-input：使用 input 命令')
    screenshot_transport = EnumField(['auto', 'adb', 'vm_network'], 'auto', '截图传输方式', 'auto：在 adb 连接较慢时尝试 vm_network。\nadb：总是使用 adb')
    aah_agent_compress = Field(bool, False, 'aah-agent 截图压缩', '使用 lz4 压缩截图数据，提高截图速度，但同时提高 CPU 占用。')
    aosp_screencap_encoding = EnumField(['auto', 'raw', 'gzip', 'png'], 'auto', 'AOSP screencap 截图压缩', '仅通过 adb 传输时可用，raw 为不压缩。')
    touch_x_min = Field(int, 0, '触摸 X 轴最小值', '触摸 X 轴的最小值，用于计算触摸坐标。')
    touch_x_max = Field(int, 0, '触摸 X 轴最大值', '触摸 X 轴的最大值，用于计算触摸坐标。')
    touch_y_min = Field(int, 0, '触摸 Y 轴最小值', '触摸 Y 轴的最小值，用于计算触摸坐标。')
    touch_y_max = Field(int, 0, '触摸 Y 轴最大值', '触摸 Y 轴的最大值，用于计算触摸坐标。')
    touch_event = Field(str, '', '触摸事件', '触摸事件 device')


class root(Schema):
    __version__ = 5
    @Namespace('ADB 控制设置')
    class device:
        adb_binary = Field(str, '', 'ADB 可执行文件', """需要启动 adb server 时，使用的 adb 命令。\n为空时则尝试: 1. PATH 中的 adb；2. ADB/{sys.platform}/adb; 3. 查找 Android SDK（ANDROID_SDK_ROOT 和默认安装目录）""")
        adb_always_use_device = Field(str, '', '自动连接设备', '自动选择设备进行连接时，只选择此设备。')
        screenshot_rate_limit = Field(int, -1, '截图频率限制', '每秒最多截图次数，超出限制时直接返回上次截图。0 表示不限制，-1 表示根据上次截图耗时自动限制。')
        @Namespace('设备列表')
        class extra_enumerators:
            vbox_emulators = Field(bool, True, '尝试探测基于 VirtualBox 的模拟器（Windows）', '通过 VirtualBox COM API 探测正在运行的模拟器')
            bluestacks_hyperv = Field(bool, True, '尝试探测 Bluestacks (Hyper-V) 设备（Windows）', '通过 Host Compute System 和 Host Compute Network API 探测正在运行的 Bluestacks Hyper-V 实例')
            append = ListField(str, ['127.0.0.1:5555', '127.0.0.1:7555'], '追加 ADB 端口', '在设备列表中追加以下 ADB TCP/IP 端口')
        @Namespace('设备默认设置')
        class defaults(ControllerConfig):
            pass
        
        adb_server = Field(str, '127.0.0.1:5037', 'ADB server 端口', '大部分情况下不需要修改。')
    @Namespace('作战模块')
    class combat:
        @Namespace('企鹅物流数据统计')
        class penguin_stats:
            enabled = Field(bool, False, '掉落汇报', '将关卡掉落上传到企鹅物流数据 (penguin-stats.io)')
            endpoint = EnumField(['global', 'cn'], 'global', '企鹅物流数据统计 API 端点', 'global: 全球站；cn: 中国镜像')
            uid = Field(str, '', '用户 ID', '用户 ID 仅用来标记您的上传身份。在不同设备上使用此 ID 登录，可让掉落数据集中于一个账号下，方便管理上传以及查看个人掉落数据。如果为空，则在下一次上传时创建并存储到配置中。')
            report_special_item = Field(bool, True, '汇报特殊活动物品', '汇报掉率随活动进度变化的特殊活动物品')
        @Namespace('代理指挥失误')
        class mistaken_delegation:
            settle = Field(bool, False, '以 2 星结算关卡')
            skip = Field(bool, True, '跳过失误关卡', '跳过失误关卡的后续次数')
    @Namespace('作战计划')
    class plan:
        calc_mode = EnumField(['online', 'local-aog'], 'online', '计算方式', 'online: 从企鹅物流数据统计接口获取刷图计划\nlocal-aog: 本地计算刷图计划, 使用 aog 推荐的关卡优化')
    @Namespace('关卡导航')
    class stage_navigator:
        ocr_backend = EnumField(['svm', 'dnn'], 'svm', '自动选关使用的 OCR 后端')
    @Namespace('OCR 设置（即将弃用）')
    class ocr:
        backend = EnumField(['auto', 'tesseract', 'baidu'], 'auto', '默认 OCR 后端')
        @Namespace('百度 OCR API 设置')
        class baidu_api:
            enable = Field(bool, False)
            app_id = Field(str, 'AAAZZZ')
            app_key = Field(str, 'AAAZZZ')
            app_secret = Field(str, 'AAAZZZ')
    @Namespace('一键长草设置')
    class grass_on_aog:
        exclude = ListField(str, ['固源岩组'], '不刷以下材料')

    debug = Field(bool, False)
