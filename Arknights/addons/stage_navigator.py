
import logging
from random import randint, uniform
logger = logging.getLogger(__name__)

class StageNavigator:
    def is_stage_supported():
        pass
    def find_and_tap(self, partition, target):
        import imgreco.map
        lastpos = None
        while True:
            screenshot = self.adb.screenshot()
            recoresult = imgreco.map.recognize_map(screenshot, partition)
            if recoresult is None:
                # TODO: retry
                logger.error('未能定位关卡地图')
                raise RuntimeError('recognition failed')
            if target in recoresult:
                pos = recoresult[target]
                logger.info('目标 %s 坐标: %s', target, pos)
                if lastpos is not None and tuple(pos) == tuple(lastpos):
                    logger.error('拖动后坐标未改变')
                    raise RuntimeError('拖动后坐标未改变')
                if 0 < pos[0] < self.viewport[0]:
                    logger.info('目标在可视区域内，点击')
                    self.adb.touch_tap(pos, offsets=(5, 5))
                    self.__wait(3)
                    break
                else:
                    lastpos = pos
                    originX = self.viewport[0] // 2 + randint(-100, 100)
                    originY = self.viewport[1] // 2 + randint(-100, 100)
                    if pos[0] < 0:  # target in left of viewport
                        logger.info('目标在可视区域左侧，向右拖动')
                        # swipe right
                        diff = -pos[0]
                        if abs(diff) < 100:
                            diff = 120
                        diff = min(diff, self.viewport[0] - originX)
                    elif pos[0] > self.viewport[0]:  # target in right of viewport
                        logger.info('目标在可视区域右侧，向左拖动')
                        # swipe left
                        diff = self.viewport[0] - pos[0]
                        if abs(diff) < 100:
                            diff = -120
                        diff = max(diff, -originX)
                    self.adb.touch_swipe2((originX, originY), (diff * 0.7 * uniform(0.8, 1.2), 0), max(250, diff / 2))
                    self.__wait(5)
                    continue

            else:
                raise KeyError((target, partition))

    def find_and_tap_episode_by_ocr(self, target):
        import imgreco.map
        import imgreco.stage_ocr
        from resources.imgreco.map_vectors import ep2region, region2ep
        target_region = ep2region.get(target)
        if target_region is None:
            logger.error(f'未能定位章节区域, target: {target}')
            raise RuntimeError('recognition failed')
        vw, vh = imgreco.common.get_vwvh(self.viewport)
        episode_tag_rect = tuple(map(int, (34.861*vh, 40.139*vh, 50.139*vh, 43.194*vh)))
        next_ep_region_rect = (6.389*vh, 73.750*vh, 33.889*vh, 80.417*vh)
        prev_ep_region_rect = (6.389*vh, 15.556*vh, 33.889*vh, 22.083*vh)
        current_ep_rect = (50*vw+19.907*vh, 28.426*vh, 50*vw+63.426*vh, 71.944*vh)
        episode_move = (400 * self.viewport[1] / 1080)

        while True:
            screenshot = self.adb.screenshot()
            current_episode_tag = screenshot.crop(episode_tag_rect)
            current_episode_str = imgreco.stage_ocr.do_img_ocr(current_episode_tag)
            logger.info(f'当前章节: {current_episode_str}')
            if not current_episode_str.startswith('EPISODE'):
                logger.error(f'章节识别失败, current_episode_str: {current_episode_str}')
                raise RuntimeError('recognition failed')
            current_episode = int(current_episode_str[7:])
            current_region = ep2region.get(current_episode)
            if current_region is None:
                logger.error(f'未能定位章节区域, current_episode: {current_episode}')
                raise RuntimeError('recognition failed')
            if current_region == target_region:
                break
            if current_region > target_region:
                logger.info(f'前往上一章节区域')
                self.tap_rect(prev_ep_region_rect)
            else:
                logger.info(f'前往下一章节区域')
                self.tap_rect(next_ep_region_rect)
        while current_episode != target:
            move = min(abs(current_episode - target), 2) * episode_move * (1 if current_episode > target else -1)
            self.__swipe_screen(move, 10, self.viewport[0] // 4 * 3)
            screenshot = self.adb.screenshot()
            current_episode_tag = screenshot.crop(episode_tag_rect)
            current_episode_str = imgreco.stage_ocr.do_img_ocr(current_episode_tag)
            logger.info(f'当前章节: {current_episode_str}')
            current_episode = int(current_episode_str[7:])

        logger.info(f'进入章节: {current_episode_str}')
        self.tap_rect(current_ep_rect)

    def find_and_tap_stage_by_ocr(self, partition, target, partition_map=None):
        import imgreco.stage_ocr
        target = target.upper()
        if partition_map is None:
            from resources.imgreco.map_vectors import stage_maps_linear
            partition_map = stage_maps_linear[partition]
        target_index = partition_map.index(target)
        while True:
            screenshot = self.adb.screenshot()
            tags_map = imgreco.stage_ocr.recognize_all_screen_stage_tags(screenshot)
            if not tags_map:
                tags_map = imgreco.stage_ocr.recognize_all_screen_stage_tags(screenshot, allow_extra_icons=True)
                if not tags_map:
                    logger.error('未能定位关卡地图')
                    raise RuntimeError('recognition failed')
            logger.debug('tags map: ' + repr(tags_map))
            pos = tags_map.get(target)
            if pos:
                logger.info('目标在可视区域内，点击')
                self.adb.touch_tap(pos, offsets=(5, 5))
                self.__wait(1)
                return

            known_indices = [partition_map.index(x) for x in tags_map.keys() if x in partition_map]

            originX = self.viewport[0] // 2 + randint(-100, 100)
            originY = self.viewport[1] // 2 + randint(-100, 100)
            move = randint(self.viewport[0] // 4, self.viewport[0] // 3)

            if all(x > target_index for x in known_indices):
                logger.info('目标在可视区域左侧，向右拖动')
            elif all(x < target_index for x in known_indices):
                move = -move
                logger.info('目标在可视区域右侧，向左拖动')
            else:
                logger.error('未能定位关卡地图')
                raise RuntimeError('recognition failed')
            self.adb.touch_swipe2((originX, originY), (move, max(250, move // 2)))
            self.__wait(1)

    def find_and_tap_daily(self, partition, target, *, recursion=0):
        import imgreco.map
        screenshot = self.adb.screenshot()
        recoresult = imgreco.map.recognize_daily_menu(screenshot, partition)
        if target in recoresult:
            pos, conf = recoresult[target]
            logger.info('目标 %s 坐标=%s 差异=%f', target, pos, conf)
            offset = self.viewport[1] * 0.12  ## 24vh * 24vh range
            self.tap_rect((*(pos - offset), *(pos + offset)))
        else:
            if recursion == 0:
                originX = self.viewport[0] // 2 + randint(-100, 100)
                originY = self.viewport[1] // 2 + randint(-100, 100)
                if partition == 'material':
                    logger.info('目标可能在可视区域左侧，向右拖动')
                    offset = self.viewport[0] * 0.2
                elif partition == 'soc':
                    logger.info('目标可能在可视区域右侧，向左拖动')
                    offset = -self.viewport[0] * 0.2
                else:
                    logger.error('未知类别')
                    raise StopIteration()
                self.adb.touch_swipe2((originX, originY), (offset, 0), 400)
                self.__wait(2)
                self.find_and_tap_daily(partition, target, recursion=recursion+1)
            else:
                logger.error('未找到目标，是否未开放关卡？')

    def goto_stage_by_ocr(self, stage):
        import imgreco.main
        import imgreco.map
        path = stage_path.get_stage_path(stage)
        self.back_to_main()
        logger.info('进入作战')
        self.tap_quadrilateral(imgreco.main.get_ballte_corners(self.adb.screenshot()))
        self.__wait(TINY_WAIT)
        if path[0] == 'main':
            vw, vh = imgreco.common.get_vwvh(self.viewport)
            self.tap_rect((14.316*vw, 89.815*vh, 28.462*vw, 99.815*vh))
            self.find_and_tap_episode_by_ocr(int(path[1][2:]))
            self.find_and_tap_stage_by_ocr(path[1], path[2])
        elif path[0] == 'material' or path[0] == 'soc':
            logger.info('选择类别')
            self.tap_rect(imgreco.map.get_daily_menu_entry(self.viewport, path[0]))
            self.find_and_tap_daily(path[0], path[1])
            self.find_and_tap(path[1], path[2])
        else:
            raise NotImplementedError()
