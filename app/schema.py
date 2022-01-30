from __future__ import annotations
from collections import OrderedDict
from collections.abc import Mapping
from typing import ClassVar, Sequence, Type, TypeVar, Generic, Optional

FieldType = TypeVar('FieldType')
ElementType = TypeVar('ElementType')
SubType = TypeVar('SubType')
class Field(Generic[FieldType]):
    def __init__(self, type: Type[FieldType], default: FieldType, title: str = None, doc: str = None):
        self.type = type
        self.default = default
        self.title = title
        self.doc = doc
        self.name: str = ''  # will be set later

    def __set_name__(self, owner: Type[Schema], name: str):
        self.name = name
        if not hasattr(owner, '_fields'):
            owner._fields = OrderedDict()
        owner._fields[name] = self

    def __get__(self, instance: Schema, owner: Type[Schema]) -> FieldType:
        if instance is None:
            return self
        return instance._store[self.name]

    def __set__(self, instance: Schema, value: FieldType):
        if value is not None:
            if not isinstance(value, self.type):
                raise TypeError(f'{value} is not {self.type}')
        instance._store[self.name] = value

class EnumField(Field[FieldType]):
    def __init__(self, values: Sequence[FieldType], default: FieldType, title=None, doc=None):
        super().__init__(type(values[0]), default, title, doc)
        self.values = values

    def __set__(self, instance: Schema, value: FieldType):
        if value not in self.values:
            raise TypeError(f'{value} is not in {self.values}')
        super().__set__(instance, value)

class ListField(Field[list[ElementType]]):
    def __init__(self, element_type: Type[ElementType], default: list[ElementType], title=None, doc=None):
        super().__init__(list, default, title, doc)
        self.element_type = element_type

    def __set__(self, instance: Schema, value: list[ElementType]):
        if value is not None:
            if not all(isinstance(e, self.element_type) for e in value):
                raise TypeError(f'{value} is not {self.element_type}')
        super().__set__(instance, value)


class Namespace(Field[SubType]):
    def __init__(self, title=None, doc=None):
        super().__init__(None, None, title, doc)

    def __call__(self, subtype: Type[SubType]) -> SubType:
        if not issubclass(subtype, Schema):
            subtype = type(subtype.__name__, (Schema, subtype), {k: v for k, v in subtype.__dict__.items() if isinstance(v, Field)})
        self.type = subtype
        return self

    def __set_name__(self, owner: Type[Schema], name: str):
        super().__set_name__(owner, name)
        self.type._parent_schema = self.type

    def __get__(self, instance: Schema, owner: Type[Schema]) -> SubType:
        if instance is None:
            return self
        return instance._namespaces[self.name]
    
    def __set__(self, instance, value):
        raise AttributeError('Namespace is read-only')

class Schema:
    _parent_schema: ClassVar[Optional[Type[Schema]]] = None
    def __init__(self, store: Optional[Mapping] = None, parent: Optional[Schema] = None):
        if store is None:
            store = _generate_default_store(self.__class__)
        self._store = store
        self._namespaces = {}
        self._parent = parent
        self._dirty = False
        for name, defn in self.__class__.__dict__.items():
            if isinstance(defn, Namespace):
                self._namespaces[name] = defn.type(store[name])
    def _set_dirty(self):
        if self._parent is not None:
            self._parent._set_dirty()
        else:
            self._dirty = True

def _generate_default_store(cls: Type[Schema], indent=0):
    import ruamel.yaml
    ydoc = ruamel.yaml.CommentedMap()
    first_field = True
    for name, field in cls.__dict__.items():
        if name.startswith('_'):
            continue
        if isinstance(field, Field):
            comment_lines = []
            if first_field:
                first_field = False
            else:
                comment_lines.append('')
            if isinstance(field, Namespace):
                ydoc[name] = _generate_default_store(field.type, indent + 2)
            else:
                ydoc[name] = field.default
            if field.title:
                comment_lines.append(field.title)
            if field.doc:
                comment_lines.append(field.doc)
            comment = '\n'.join(comment_lines)
            if comment:
                ydoc.yaml_set_comment_before_after_key(name, before=comment, indent=indent)
    return ydoc


def is_dirty(schema: Schema):
    return schema._dirty


class root(Schema):
    __version__ = 1
    debug = Field(bool, False)
    @Namespace('设备连接')
    class device:
        adb_server = Field(str, '127.0.0.1:5037', 'ADB server 端口', '如 ADB server 端口冲突（表现为 server 频繁退出），可尝试更换端口。')
        adb_binary = Field(str, '', 'ADB 可执行文件', """需要启动 adb server 时，使用的 adb 命令。\n为空时则尝试: 1. PATH 中的 adb；2. ADB/{sys.platform}/adb; 3. 查找 Android SDK（ANDROID_SDK_ROOT 和默认安装目录）""")
        adb_always_use_device = Field(str, '', '只连接特定设备')
        @Namespace('额外的设备枚举逻辑')
        class extra_enumerators:
            bluestacks_hyperv = Field(bool, True, '尝试探测 Bluestacks (Hyper-V) 设备')
            append = ListField(str, ['127.0.0.1:5555', '127.0.0.1:7555'], '尝试连接 ADB 端口', '在设备列表中追加以下 ADB TCP/IP 端口')
        compat_screenshot = Field(bool, True, '使用兼容性较好（但较慢）的截图方式')
        workaround_slow_emulator_adb = EnumField(['auto', 'never', 'always'], 'auto', '尝试优化 ADB 数据传输', '通过 adb 传输模拟器截图数据较慢时，尝试绕过 adbd 传输截图数据\n模拟器判断逻辑：1. 设备名称以 "emulator-" 或 "127.0.0.1:" 开头；2. ro.product.board 包含 goldfish（SDK emulator）或存在 vboxguest 模块')
        cache_screenshot = Field(bool, True, '截图缓存', '如果两次截图间隔小于上次截图耗时，则直接使用上次的截图')
    @Namespace('作战模块', '回复体力设置已移除，请使用命令行参数或在 GUI 中设置')
    class combat:
        @Namespace('企鹅物流数据统计')
        class penguin_stats:
            enabled = Field(bool, False, '掉落汇报', '将关卡掉落上传到企鹅物流数据 (penguin-stats.io)')
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
        backend = EnumField(['auto', 'tesseract', 'windows_media_ocr', 'baidu'], 'auto', '默认 OCR 后端')
        @Namespace('百度 OCR API 设置')
        class baidu_api:
            enable = Field(bool, False)
            app_id = Field(str, 'AAAZZZ')
            app_key = Field(str, 'AAAZZZ')
            app_secret = Field(str, 'AAAZZZ')
    @Namespace('一键长草设置')
    class grass_on_aog:
        exclude = ListField(str, ['固源岩组'], '不刷以下材料')

