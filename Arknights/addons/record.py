import os
import logging
import re
import json
import imgreco.imgops

logger = logging.getLogger(__name__)

class RecordAddon:
    def create_custom_record(self, record_name, roi_size=64, wait_seconds_after_touch=1,
                             description='', back_to_main=True, prefer_mode='match_template', threshold=0.7):
        record_dir = os.path.join(os.path.realpath(os.path.join(__file__, '../../')),
                                  os.path.join('custom_record/', record_name))
        if os.path.exists(record_dir):
            c = input('已存在同名的记录, y 覆盖, n 退出: ')
            if c.strip().lower() != 'y':
                return
            import shutil
            shutil.rmtree(record_dir)
        os.mkdir(record_dir)

        if back_to_main:
            self.back_to_main()

        EVENT_LINE_RE = re.compile(r"(\S+): (\S+) (\S+) (\S+)$")
        records = []
        record_data = {
            'screen_width': self.viewport[0],
            'screen_height': self.viewport[1],
            'description': description,
            'prefer_mode': prefer_mode,
            'back_to_main': back_to_main,
            'records': records
        }
        half_roi = roi_size // 2
        logger.info('滑动屏幕以退出录制.')
        logger.info('开始录制, 请点击相关区域...')
        sock = self.adb.device_session_factory().shell_stream('getevent')
        f = sock.makefile('rb')
        while True:
            x = 0
            y = 0
            point_list = []
            touch_down = False
            screen = self.adb.screenshot()
            while True:
                line = f.readline().decode('utf-8', 'replace').strip()
                # print(line)
                match = EVENT_LINE_RE.match(line.strip())
                if match is not None:
                    dev, etype, ecode, data = match.groups()
                    if '/dev/input/event5' != dev:
                        continue
                    etype, ecode, data = int(etype, 16), int(ecode, 16), int(data, 16)
                    # print(dev, etype, ecode, data)

                    if (etype, ecode) == (1, 330):
                        touch_down = (data == 1)

                    if touch_down:
                        if 53 == ecode:
                            x = data
                        elif 54 == ecode:
                            y = data
                        elif (etype, ecode, data) == (0, 0, 0):
                            # print(f'point: ({x}, {y})')
                            point_list.append((x, y))
                    elif (etype, ecode, data) == (0, 0, 0):
                        break
            logger.debug(f'point_list: {point_list}')
            if len(point_list) == 1:
                point = point_list[0]
                x1 = max(0, point[0] - half_roi)
                x2 = min(self.viewport[0] - 1, point[0] + half_roi)
                y1 = max(0, point[1] - half_roi)
                y2 = min(self.viewport[1] - 1, point[1] + half_roi)
                roi = screen.crop((x1, y1, x2, y2))
                step = len(records)
                roi.save(os.path.join(record_dir, f'step{step}.png'))
                record = {'point': point, 'img': f'step{step}.png', 'type': 'tap',
                          'wait_seconds_after_touch': wait_seconds_after_touch,
                          'threshold': threshold, 'repeat': 1, 'raise_exception': True}
                logger.info(f'record: {record}')
                records.append(record)
                if wait_seconds_after_touch:
                    logger.info(f'请等待 {wait_seconds_after_touch}s...')
                    self.__wait(wait_seconds_after_touch)

                logger.info('继续...')
            elif len(point_list) > 1:
                # 滑动时跳出循环
                c = input('是否退出录制[Y/n]:')
                if c.strip().lower() != 'n':
                    logger.info('停止录制...')
                    break
                else:
                    # todo 处理屏幕滑动
                    continue
        with open(os.path.join(record_dir, f'record.json'), 'w', encoding='utf-8') as f:
            json.dump(record_data, f, ensure_ascii=False, indent=4, sort_keys=True)

    def replay_custom_record(self, record_name, mode=None, back_to_main=None):
        from util import cvimage as Image
        record_dir = os.path.join(os.path.realpath(os.path.join(__file__, '../../')),
                                  os.path.join('custom_record/', record_name))
        if not os.path.exists(record_dir):
            logger.error(f'未找到相应的记录: {record_name}')
            raise RuntimeError(f'未找到相应的记录: {record_name}')

        with open(os.path.join(record_dir, 'record.json'), 'r', encoding='utf-8') as f:
            record_data = json.load(f)
        logger.info(f'record description: {record_data.get("description")}')
        records = record_data['records']
        if mode is None:
            mode = record_data.get('prefer_mode', 'match_template')
        if mode not in ('match_template', 'point'):
            logger.error(f'不支持的模式: {mode}')
            raise RuntimeError(f'不支持的模式: {mode}')
        if back_to_main is None:
            back_to_main = record_data.get('back_to_main', True)
        if back_to_main:
            self.back_to_main()
        record_height = record_data['screen_height']
        ratio = record_height / self.viewport[1]
        x, y = 0, 0
        for record in records:
            if record['type'] == 'tap':
                repeat = record.get('repeat', 1)
                raise_exception = record.get('raise_exception', True)
                threshold = record.get('threshold', 0.7)
                for _ in range(repeat):
                    if mode == 'match_template':
                        screen = self.adb.screenshot()
                        gray_screen = screen.convert('L')
                        if ratio != 1:
                            gray_screen = gray_screen.resize((int(self.viewport[0] * ratio), record_height))
                        template = Image.open(os.path.join(record_dir, record['img'])).convert('L')
                        (x, y), r = imgreco.imgops.match_template(gray_screen, template)
                        x = x // ratio
                        y = y // ratio
                        logger.info(f'(x, y), r, record: {(x, y), r, record}')
                        if r < threshold:
                            if raise_exception:
                                logger.error('无法识别的图像: ' + record['img'])
                                raise RuntimeError('无法识别的图像: ' + record['img'])
                            break
                    elif mode == 'point':
                        # 这个模式屏幕尺寸宽高比必须与记录中的保持一至
                        assert record_data['screen_width'] == int(self.viewport[0] * ratio)
                        x, y = record['point']
                        x = x // ratio
                        y = y // ratio
                    self.adb.touch_tap((x, y), offsets=(5, 5))
                    if record.get('wait_seconds_after_touch'):
                        self.__wait(record['wait_seconds_after_touch'])
