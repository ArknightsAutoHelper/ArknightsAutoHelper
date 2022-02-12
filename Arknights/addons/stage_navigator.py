from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable, Any, Sequence, ClassVar, Optional, Type

from automator import AddonBase, cli_command
from .common import CommonAddon
from .combat import CombatAddon, _parse_opt
from dataclasses import dataclass
from collections import OrderedDict
from random import randint, uniform
from Arknights.flags import *

from resources.imgreco.map_vectors import stage_maps_linear, is_invalid_stage
known_stages_ocr = [x for v in stage_maps_linear.values() for x in v]

def _isnumchar(ch):
    return len(ch) == 1 and '0' <= ch <= '9'

def get_stage_path(stage):
    parts = stage.split('-')
    part0 = parts[0]
    if _isnumchar(part0[-1]):  # '1-7', 'S4-1', etc
        return ['main', 'ep0' + parts[0][-1], stage]
    elif part0 in ('LS', 'AP', 'SK', 'CE', 'CA'):
        return ['material', part0, stage]
    elif part0 == 'PR' and parts[1] in ('A', 'B', 'C', 'D'):
        return ['soc', 'PR-' + parts[1], stage]
    return None


def is_stage_supported_ocr(stage):
    return stage in known_stages_ocr and not is_invalid_stage(stage)

@dataclass
class _custom_stage_record:
    owner: Type[AddonBase]
    name: str
    func: Callable = None
    title: Optional[str] = None
    description: Optional[str] = None
    ignore_count: bool = False

@dataclass
class _navigator_record:
    owner: Type[AddonBase]
    tag: str
    query: Callable[..., bool]
    navigate: Callable[..., None]

_custom_stage_registry: OrderedDict[str, _custom_stage_record] = OrderedDict()
_navigator_registry: list[_navigator_record] = []
class custom_stage:
    def __init__(self, name, ignore_count=False, title: Optional[str] = None, description: Optional[str] = None):
        if callable(name):
            self.fn = self.name
            self.name = name.__name__
        else:
            self.fn = None
            self.name = name
        self.ignore_count = ignore_count
        self.title = title
        self.description = description
    
    def __call__(self, func):
        self.fn = func
        return self
    
    def __set_name__(self, owner, name):
        _custom_stage_registry[self.name] = _custom_stage_record(owner, self.name, self.fn, self.title, self.description, self.ignore_count)
        setattr(owner, name, self.fn)

class navigator:
    def __init__(self, tag=None, *, query: Optional[Callable[[Type[AddonBase], str], bool]] = None, naivgate: Optional[Callable[[Type[AddonBase], str], None]] = None):
        if callable(tag):
            self._query = tag
            self.tag = None
        else:
            self.tag = tag
            self._query = query
        self._navigate = naivgate
    def __call__(self, func):
        self._query = func
        return self
    def navigate(self, fn):
        self._navigate = fn
        return fn
    def __set_name__(self, owner, name):
        if self._query is None:
            raise ValueError('navigator must have a query function')
        if self._navigate is None:
            raise ValueError('navigator must have a navigate function')
        if self.tag is None:
            self.tag = owner.__name__
        _navigator_registry.append(_navigator_record(owner, self.tag, self._query, self._navigate))
        setattr(owner, name, self.navigate)

def _auto_extra_help():
    append_helptext = ['']
    for name, record in _custom_stage_registry.items():
        text = f"            {record.name}"
        if record.title is not None:
            text += f"\t{record.title}"
            if record.description is not None:
                text += f": {record.description}"
        append_helptext.append(text)
    return '\n'.join(append_helptext)

class StageNavigator(AddonBase):
    def on_attach(self) -> None:
        self.extra_handlers: list[tuple[Callable[[str], bool], Callable[[str], Any]]] = []
        self.handler_cache = {}

    def is_stage_supported(self, stage):
        if stage in self.handler_cache:
            return True
        for record in _navigator_registry:
            self.logger.debug("querying %s for stage %s navigation", record.tag, stage)
            result = record.query(self.addon(record.owner), stage)
            if result:
                self.handler_cache[stage] = lambda stage: record.navigate(self.addon(record.owner), stage)
                return True
        return False

    def goto_stage(self, stage):
        if not self.is_stage_supported(stage):
            raise ValueError(stage)
        handler = self.handler_cache[stage]
        handler(stage)

    def find_and_tap(self, partition, target):
        import imgreco.map
        lastpos = None
        while True:
            screenshot = self.device.screenshot()
            recoresult = imgreco.map.recognize_map(screenshot, partition)
            if recoresult is None:
                # TODO: retry
                self.logger.error('未能定位关卡地图')
                raise RuntimeError('recognition failed')
            if target in recoresult:
                pos = recoresult[target]
                self.logger.info('目标 %s 坐标: %s', target, pos)
                if lastpos is not None and tuple(pos) == tuple(lastpos):
                    self.logger.error('拖动后坐标未改变')
                    raise RuntimeError('拖动后坐标未改变')
                if 0 < pos[0] < self.viewport[0]:
                    self.logger.info('目标在可视区域内，点击')
                    self.device.touch_tap(pos, offsets=(5, 5))
                    self.delay(3)
                    break
                else:
                    lastpos = pos
                    originX = self.viewport[0] // 2 + randint(-100, 100)
                    originY = self.viewport[1] // 2 + randint(-100, 100)
                    if pos[0] < 0:  # target in left of viewport
                        self.logger.info('目标在可视区域左侧，向右拖动')
                        # swipe right
                        diff = -pos[0]
                        if abs(diff) < 100:
                            diff = 120
                        diff = min(diff, self.viewport[0] - originX)
                    elif pos[0] > self.viewport[0]:  # target in right of viewport
                        self.logger.info('目标在可视区域右侧，向左拖动')
                        # swipe left
                        diff = self.viewport[0] - pos[0]
                        if abs(diff) < 100:
                            diff = -120
                        diff = max(diff, -originX)
                    self.device.touch_swipe2((originX, originY), (diff * 0.7 * uniform(0.8, 1.2), 0), max(250, diff / 2))
                    self.delay(5)
                    continue

            else:
                raise KeyError((target, partition))

    def find_and_tap_episode_by_ocr(self, target):
        import imgreco.common
        import imgreco.map
        import imgreco.stage_ocr
        from resources.imgreco.map_vectors import ep2region, region2ep
        target_region = ep2region.get(target)
        if target_region is None:
            self.logger.error(f'未能定位章节区域, target: {target}')
            raise RuntimeError('recognition failed')
        vw, vh = imgreco.common.get_vwvh(self.viewport)
        episode_tag_rect = tuple(map(int, (34.861*vh, 40.139*vh, 50.139*vh, 43.194*vh)))
        next_ep_region_rect = (6.389*vh, 73.750*vh, 33.889*vh, 80.417*vh)
        prev_ep_region_rect = (6.389*vh, 15.556*vh, 33.889*vh, 22.083*vh)
        current_ep_rect = (50*vw+19.907*vh, 28.426*vh, 50*vw+63.426*vh, 71.944*vh)
        episode_move = (400 * self.viewport[1] / 1080)

        while True:
            screenshot = self.device.screenshot()
            current_episode_tag = screenshot.crop(episode_tag_rect)
            current_episode_str = imgreco.stage_ocr.do_img_ocr(current_episode_tag)
            self.logger.info(f'当前章节: {current_episode_str}')
            if not current_episode_str.startswith('EPISODE'):
                self.logger.error(f'章节识别失败, current_episode_str: {current_episode_str}')
                raise RuntimeError('recognition failed')
            current_episode = int(current_episode_str[7:])
            current_region = ep2region.get(current_episode)
            if current_region is None:
                self.logger.error(f'未能定位章节区域, current_episode: {current_episode}')
                raise RuntimeError('recognition failed')
            if current_region == target_region:
                break
            if current_region > target_region:
                self.logger.info(f'前往上一章节区域')
                self.tap_rect(prev_ep_region_rect)
            else:
                self.logger.info(f'前往下一章节区域')
                self.tap_rect(next_ep_region_rect)
        while current_episode != target:
            move = min(abs(current_episode - target), 2) * episode_move * (1 if current_episode > target else -1)
            self.swipe_screen(move, 10, self.viewport[0] // 4 * 3)
            screenshot = self.device.screenshot()
            current_episode_tag = screenshot.crop(episode_tag_rect)
            current_episode_str = imgreco.stage_ocr.do_img_ocr(current_episode_tag)
            self.logger.info(f'当前章节: {current_episode_str}')
            current_episode = int(current_episode_str[7:])

        self.logger.info(f'进入章节: {current_episode_str}')
        self.tap_rect(current_ep_rect)

    def find_and_tap_stage_by_ocr(self, partition, target, partition_map=None):
        import imgreco.stage_ocr
        target = target.upper()
        if partition_map is None:
            from resources.imgreco.map_vectors import stage_maps_linear
            partition_map = stage_maps_linear[partition]
        target_index = partition_map.index(target)
        while True:
            screenshot = self.device.screenshot()
            tags_map = imgreco.stage_ocr.recognize_all_screen_stage_tags(screenshot)
            if not tags_map:
                tags_map = imgreco.stage_ocr.recognize_all_screen_stage_tags(screenshot, allow_extra_icons=True)
                if not tags_map:
                    self.logger.error('未能定位关卡地图')
                    raise RuntimeError('recognition failed')
            self.logger.debug('tags map: ' + repr(tags_map))
            pos = tags_map.get(target)
            if pos:
                self.logger.info('目标在可视区域内，点击')
                self.device.touch_tap(pos, offsets=(5, 5))
                self.delay(1)
                return

            known_indices = [partition_map.index(x) for x in tags_map.keys() if x in partition_map]

            originX = self.viewport[0] // 2 + randint(-100, 100)
            originY = self.viewport[1] // 2 + randint(-100, 100)
            move = randint(self.viewport[0] // 4, self.viewport[0] // 3)

            if all(x > target_index for x in known_indices):
                self.logger.info('目标在可视区域左侧，向右拖动')
            elif all(x < target_index for x in known_indices):
                move = -move
                self.logger.info('目标在可视区域右侧，向左拖动')
            else:
                self.logger.error('未能定位关卡地图')
                raise RuntimeError('recognition failed')
            self.device.touch_swipe2((originX, originY), (move, max(250, move // 2)))
            self.delay(1)

    def find_and_tap_daily(self, partition, target, *, recursion=0):
        import imgreco.map
        screenshot = self.device.screenshot()
        recoresult = imgreco.map.recognize_daily_menu(screenshot, partition)
        if target in recoresult:
            pos, conf = recoresult[target]
            self.logger.info('目标 %s 坐标=%s 差异=%f', target, pos, conf)
            offset = self.viewport[1] * 0.12  ## 24vh * 24vh range
            self.tap_rect((*(pos - offset), *(pos + offset)))
        else:
            if recursion == 0:
                originX = self.viewport[0] // 2 + randint(-100, 100)
                originY = self.viewport[1] // 2 + randint(-100, 100)
                if partition == 'material':
                    self.logger.info('目标可能在可视区域左侧，向右拖动')
                    offset = self.viewport[0] * 0.2
                elif partition == 'soc':
                    self.logger.info('目标可能在可视区域右侧，向左拖动')
                    offset = -self.viewport[0] * 0.2
                else:
                    self.logger.error('未知类别')
                    raise StopIteration()
                self.device.touch_swipe2((originX, originY), (offset, 0), 400)
                self.delay(2)
                self.find_and_tap_daily(partition, target, recursion=recursion+1)
            else:
                self.logger.error('未找到目标，是否未开放关卡？')

    @navigator('builtin')
    def is_stage_supported_builtin(self, c_id):
        result = is_stage_supported_ocr(c_id)
        return result

    @is_stage_supported_builtin.navigate
    def goto_stage_builtin(self, stage):
        import imgreco.common
        import imgreco.main
        import imgreco.map
        path = get_stage_path(stage)
        self.addon(CommonAddon).back_to_main()
        self.logger.info('进入作战')
        self.tap_quadrilateral(imgreco.main.get_ballte_corners(self.device.screenshot()))
        self.delay(TINY_WAIT)
        if path[0] == 'main':
            vw, vh = imgreco.common.get_vwvh(self.viewport)
            self.tap_rect((14.316*vw, 89.815*vh, 28.462*vw, 99.815*vh))
            self.find_and_tap_episode_by_ocr(int(path[1][2:]))
            self.find_and_tap_stage_by_ocr(path[1], path[2])
        elif path[0] == 'material' or path[0] == 'soc':
            self.logger.info('选择类别')
            self.tap_rect(imgreco.map.get_daily_menu_entry(self.viewport, path[0]))
            self.find_and_tap_daily(path[0], path[1])
            self.find_and_tap(path[1], path[2])
        else:
            raise NotImplementedError()

    def navigate_and_combat(self,  # 完整的战斗模块
                            c_id: str,  # 选择的关卡
                            set_count=1000):  # 作战次数
        c_id = c_id.upper()
        if self.is_stage_supported(c_id):
            self.goto_stage(c_id)
        else:
            self.logger.error('不支持的关卡：%s', c_id)
            raise ValueError(c_id)
        return self.addon(CombatAddon).combat_on_current_stage(set_count, c_id)

    def main_handler(self, task_list: Sequence[tuple[str, int]]):
        if len(task_list) == 0:
            self.logger.fatal("任务清单为空!")
            return

        for c_id, count in task_list:
            self.logger.info("开始 %s", c_id)
            if c_id in _custom_stage_registry:
                record = _custom_stage_registry[c_id]
                record.func(self.addon(record.owner), count)
            else:
                flag = self.navigate_and_combat(c_id, count)

        self.logger.info("任务清单执行完毕")

    def parse_target_desc(self, args):
        result = []
        it = iter(args)
        while True:
            try:
                current = next(it)
            except StopIteration:
                break
            if current in _custom_stage_registry:
                record = _custom_stage_registry[current]
                if record.ignore_count:
                    result.append((current, None))
                    continue
            else:
                if not self.is_stage_supported(current):
                    raise ValueError('不支持的关卡：%s' % current)
            try:
                count_str = next(it)
                count = int(count_str)
            except StopIteration:
                raise ValueError('count expected after %r' % current)
            except ValueError:
                raise ValueError('invalid count: %r' % count)
            result.append((current, count))
        return result

    @cli_command('auto')
    def cli_auto(self, argv):
        """
        auto [+-rR[N]] TARGET_DESC [TARGET_DESC]...
        按顺序挑战指定关卡。
        TARGET_DESC 可以是：
            1-7 10\t特定主线、活动关卡（1-7）10 次
        """
        ops = _parse_opt(argv)
        arglist = argv[1:]
        if len(arglist) == 0:
            print('usage: auto [+-rR] stage1 count1 [stage2 count2] ...')
            return 1
        it = iter(arglist)
        tasks = self.parse_target_desc(arglist)

        for op in ops:
            op(self)
        with self.helper.frontend.context:
            self.main_handler(task_list=tasks)
        return 0

    @cli_auto.dynamic_help
    def cli_auto_help(self):
        return self.cli_auto.__doc__.rstrip() + _auto_extra_help()
