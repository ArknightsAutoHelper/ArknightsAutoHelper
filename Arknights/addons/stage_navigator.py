from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable, Any

from Arknights.helper import AddonBase
from .common import CommonAddon
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


class StageNavigator(AddonBase):
    def on_attach(self) -> None:
        self.extra_handlers: list[tuple[Callable[[str], bool], Callable[[str], Any]]] = []

    def register_navigator(self, tag: str, predicate: Callable[[str], bool], navigator: Callable[[str], Any]):
        self.extra_handlers.append((tag, predicate, navigator))

    def is_stage_supported(self, c_id):
        result = is_stage_supported_ocr(c_id)
        if not result:
            for tag, predicate, handler in self.extra_handlers:
                self.logger.debug("querying %s for stage %s navigation", tag, c_id)
                result = predicate(c_id)
                if result:
                    break
        return result

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

    def goto_stage(self, stage):
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
