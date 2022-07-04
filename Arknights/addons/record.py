import json
import logging

import os
import re
import time
from random import randint

import app
import imgreco.imgops
from automator import AddonBase, cli_command
from Arknights.addons.common import CommonAddon
from util import cvimage as Image

record_basedir = app.writable_root.joinpath('custom_record')
EVENT_LINE_RE = re.compile(r"(\S+): (\S+) (\S+) (\S+)$")
DEVICE_RE = re.compile(r'add device.*(/dev/input/event\d+)')
MIN_RE = re.compile(r'min (\d+)')
MAX_RE = re.compile(r'max (\d+)')


def _apply_ratio(point, ratio):
    x, y = point
    x = x // ratio
    y = y // ratio
    return x, y


class RecordAddon(AddonBase):
    def __init__(self, helper):
        super().__init__(helper)
        self.touch_event = None
        self.touch_x_min = None
        self.touch_x_max = None
        self.touch_y_min = None
        self.touch_y_max = None

    def ensure_device_event(self):
        self.touch_event = self.control.device_config.touch_event
        if self.touch_event == '':
            self.touch_event = self.detect_device_event()
        self.touch_x_min = self.control.device_config.touch_x_min
        self.touch_x_max = self.control.device_config.touch_x_max
        self.touch_y_min = self.control.device_config.touch_y_min
        self.touch_y_max = self.control.device_config.touch_y_max

    def detect_device_event(self):
        self.logger.info('可能需要 root 权限才能检测设备事件, 建议使用模拟器.')
        self.logger.info('检测中...')
        data = self.control.adb.shell('getevent -pl')
        last_device = None
        touch_event = None
        for line in data.splitlines():
            line = line.decode('utf-8')
            self.logger.debug(line)
            if '/dev/input/' in line:
                match = DEVICE_RE.match(line)
                if match:
                    last_device = match.group(1)
            if 'ABS_MT_POSITION_X' in line:
                touch_event = last_device
                min_value = MIN_RE.search(line).group(1)
                max_value = MAX_RE.search(line).group(1)
                self.control.device_config.touch_x_min = int(min_value)
                self.control.device_config.touch_x_max = int(max_value)
            if 'ABS_MT_POSITION_Y' in line:
                touch_event = last_device
                min_value = MIN_RE.search(line).group(1)
                max_value = MAX_RE.search(line).group(1)
                self.control.device_config.touch_y_min = int(min_value)
                self.control.device_config.touch_y_max = int(max_value)
        self.control.device_config.touch_event = touch_event
        self.control.device_config.save()
        self.logger.info(f'检测完毕, touch_event: {touch_event}')
        return touch_event

    def calc_x_pos(self, x):
        x -= self.touch_x_min
        return int(x / (self.touch_x_max - self.touch_x_min) * self.viewport[0])

    def calc_y_pos(self, y):
        y -= self.touch_y_min
        return int(y / (self.touch_y_max - self.touch_y_min) * self.viewport[1])

    def create_custom_record(self, record_name, roi_size=64, wait_seconds_after_touch=1,
                             description='', back_to_main=True, prefer_mode='match_template', threshold=0.7):
        self.ensure_device_event()
        record_dir = record_basedir.joinpath(record_name)
        if record_dir.exists():
            c = input('已存在同名的记录, y 覆盖, n 退出: ')
            if c.strip().lower() != 'y':
                return
            import shutil
            shutil.rmtree(record_dir)
        os.mkdir(record_dir)

        if back_to_main:
            self.addon(CommonAddon).back_to_main()
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
        self.logger.info('滑动屏幕以退出录制.')
        self.logger.info('开始录制, 请点击相关区域...')
        sock = self.control.adb.shell_stream('getevent')
        f = sock.makefile('rb')
        while True:
            point_list = []
            touch_down = False
            screen = self.control.screenshot()
            x, y, st, duration = 0, 0, 0, 0
            while True:
                line = f.readline().decode('utf-8', 'replace').strip()
                # print(line)
                match = EVENT_LINE_RE.match(line.strip())
                if match is not None:
                    dev, etype, ecode, data = match.groups()
                    if self.touch_event != dev:
                        continue
                    etype, ecode, data = int(etype, 16), int(ecode, 16), int(data, 16)
                    # print(dev, etype, ecode, data)
                    if ecode == 53 or ecode == 54:
                        if st == 0:
                            st = time.time()
                        touch_down = True
                    if touch_down:
                        if 53 == ecode:
                            x = self.calc_x_pos(data)
                        elif 54 == ecode:
                            y = self.calc_y_pos(data)
                        elif (etype, ecode, data) == (0, 0, 0):
                            # print(f'point: ({x}, {y})')
                            point_list.append((x, y))
                            touch_down = False
                    elif (etype, ecode, data) == (0, 0, 0):
                        duration = time.time() - st
                        break
            self.logger.debug(f'point_list: {point_list}')
            if len(point_list) == 1:
                point = point_list[0]
                x1 = max(0, point[0] - half_roi)
                x2 = min(self.viewport[0] - 1, point[0] + half_roi)
                y1 = max(0, point[1] - half_roi)
                y2 = min(self.viewport[1] - 1, point[1] + half_roi)
                roi = screen.crop((x1, y1, x2, y2))
                step = len(records)
                roi.save(record_dir.joinpath(f'step{step}.png'))
                record = {'point': point, 'img': f'step{step}.png', 'type': 'tap',
                          'wait_seconds_after_touch': wait_seconds_after_touch,
                          'threshold': threshold, 'repeat': 1, 'raise_exception': True}
                self.logger.info(f'record: {record}')
                records.append(record)
                if wait_seconds_after_touch:
                    self.logger.info(f'请等待 {wait_seconds_after_touch}s...')
                    self.delay(wait_seconds_after_touch)

                self.logger.info('继续...')
            elif len(point_list) > 1:
                # 滑动时跳出循环
                c = input('是否退出录制[Y/n]:')
                if c.strip().lower() != 'n':
                    self.logger.info('停止录制...')
                    break
                else:
                    start_point, end_point = point_list[0], point_list[-1]
                    factor = (end_point[0] - start_point[0], end_point[1] - start_point[1])
                    record = {'start_point': start_point, 'type': 'swipe', 'factor': factor,
                              'wait_seconds_after_touch': wait_seconds_after_touch,
                              'duration': duration, 'repeat': 1, 'raise_exception': True}
                    self.logger.info(f'record: {record}')
                    records.append(record)
                    if wait_seconds_after_touch:
                        self.logger.info(f'请等待 {wait_seconds_after_touch}s...')
                        self.delay(wait_seconds_after_touch)
                    self.logger.info('继续...')
        with open(record_dir.joinpath('record.json'), 'w', encoding='utf-8') as f:
            json.dump(record_data, f, ensure_ascii=False, indent=4, sort_keys=True)

    def get_record_path(self, record_name):
        record_dir = record_basedir.joinpath(record_name)
        if not record_dir.exists():
            return None
        return record_dir

    def replay_custom_record(self, record_name, mode=None, back_to_main=None, quiet=False):
        record_dir = self.get_record_path(record_name)
        if record_dir is None:
            self.logger.error(f'未找到相应的记录: {record_name}')
            raise RuntimeError(f'未找到相应的记录: {record_name}')

        with open(record_dir.joinpath('record.json'), 'r', encoding='utf-8') as f:
            record_data = json.load(f)
        self.logger.log(logging.DEBUG if quiet else logging.INFO, f'record description: {record_data.get("description")}')
        records = record_data['records']
        if mode is None:
            mode = record_data.get('prefer_mode', 'match_template')
        if mode not in ('match_template', 'point'):
            self.logger.error(f'不支持的模式: {mode}')
            raise RuntimeError(f'不支持的模式: {mode}')
        if back_to_main is None:
            back_to_main = record_data.get('back_to_main', True)
        if back_to_main:
            self.addon(CommonAddon).back_to_main()
        record_height = record_data['screen_height']
        ratio = record_height / self.viewport[1]
        for record in records:
            if record['type'] == 'tap':
                self._do_record_tap(record, mode, ratio, record_height, record_dir, quiet, record_name, record_data)
            elif record['type'] == 'swipe':
                self._do_record_swipe(record, ratio, record_data)

    def _do_record_swipe(self, record, ratio, record_data):
        assert record_data['screen_width'] == int(self.viewport[0] * ratio)
        start_point = _apply_ratio(record['start_point'], ratio)
        factor = _apply_ratio(record['factor'], ratio)
        end_point = (start_point[0] + factor[0], start_point[1] + factor[1])
        for _ in range(record['repeat']):
            duration = record.get('duration', randint(600, 900)/1000)
            self.logger.info(f'swipe: {record}')
            self.control.input.touch_swipe(start_point[0], start_point[1], end_point[0], end_point[1],
                                           move_duration=duration)
            if record['wait_seconds_after_touch']:
                self.delay(record['wait_seconds_after_touch'])

    def _do_record_tap(self, record, mode, ratio, record_height, record_dir, quiet, record_name, record_data):
        x, y = 0, 0
        repeat = record.get('repeat', 1)
        raise_exception = record.get('raise_exception', True)
        threshold = record.get('threshold', 0.7)
        for _ in range(repeat):
            if mode == 'match_template':
                screen = self.control.screenshot()
                gray_screen = screen.convert('L')
                if ratio != 1:
                    gray_screen = gray_screen.resize((int(self.viewport[0] * ratio), record_height))
                template = Image.open(record_dir.joinpath(record['img'])).convert('L')
                (x, y), r = imgreco.imgops.match_template(gray_screen, template)
                x = x // ratio
                y = y // ratio
                self.logger.log(logging.DEBUG if quiet else logging.INFO,
                                f'(x, y), r, record, record_name: {(x, y), r, record, record_name}')
                if r < threshold:
                    if raise_exception:
                        self.logger.log(logging.DEBUG if quiet else logging.ERROR, '无法识别的图像: ' + record['img'])
                        raise RuntimeError('无法识别的图像: ' + record['img'])
                    break
            elif mode == 'point':
                # 这个模式屏幕尺寸宽高比必须与记录中的保持一至
                assert record_data['screen_width'] == int(self.viewport[0] * ratio)
                x, y = record['point']
                x = x // ratio
                y = y // ratio
                self.logger.log(logging.DEBUG if quiet else logging.INFO,
                                f'(x, y), record, record_name: {(x, y), record, record_name}')
            self.control.touch_tap((x, y), offsets=(5, 5))
            if record.get('wait_seconds_after_touch'):
                self.delay(record['wait_seconds_after_touch'])

    def try_replay_record(self, record_name, quiet=False):
        try:
            self.replay_custom_record(record_name, quiet=quiet)
            return True
        except Exception as e:
            self.logger.log(logging.DEBUG if quiet else logging.INFO, f'skip {record_name}, {e}')
            return False

    def get_records(self):
        path, dirs, files = next(os.walk(record_basedir))
        return [x for x in dirs if os.path.isfile(os.path.join(path, x, 'record.json'))]

    @cli_command('record')
    def cli_record(self, argv):
        """
        record
        操作记录模块，使用 record --help 查看帮助。
        """
        import argparse
        parser = argparse.ArgumentParser(prog='record', description='操作记录模块')
        subparsers = parser.add_subparsers(dest='subcommand', title='subcommands', required=True)

        new_parser = subparsers.add_parser('new', description='录制操作记录')
        new_parser.add_argument('--prefer-mode', choices=['match_template', 'point'], help='回放模式：模板匹配（match_template）或固定坐标（point）')
        new_parser.add_argument('--back-to-main', action='store_true', help='是否从主界面开始回放')
        new_parser.add_argument('--roi-size', type=int, help='模板匹配的大小')
        new_parser.add_argument('--wait-seconds-after-touch', type=float, help='每次点击后的等待时间')
        new_parser.add_argument('--description', help='操作记录的额外描述文本')
        new_parser.add_argument('--threshold', type=float, help='模板匹配的阈值（0-1），越接近 1 代表相似度越高')
        new_parser.add_argument('NAME', help='记录名称')

        play_parser = subparsers.add_parser('play', description='回放操作记录')
        play_parser.add_argument('--mode', choices=['match_template', 'point'], help='覆盖录制时选择的模式')
        play_parser.add_argument('--back-to-main', type=lambda x: x=='true', choices=['true', 'false'], action='store', help='覆盖录制时设置的是否回到主界面')
        play_parser.add_argument('NAME', help='记录名称')

        list_parser = subparsers.add_parser('list', description='列出已录制的操作记录')

        try:
            args_ns = parser.parse_args(argv[1:])
        except SystemExit as e:
            return e.code
        
        subcommand = args_ns.subcommand
        if subcommand == 'list':
            import shlex
            for record in self.get_records():
                print(shlex.quote(record))
        elif subcommand == 'new':
            argnames = ['roi_size', 'wait_seconds_after_touch', 'description', 'back_to_main', 'prefer_mode', 'threshold']
            kwargs = {k: vars(args_ns)[k] for k in argnames if k in args_ns}
            kwargs = {k: v for k, v in kwargs.items() if v is not None}
            self.create_custom_record(args_ns.NAME, **kwargs)
        elif subcommand == 'play':
            argnames = ['back_to_main', 'mode']
            kwargs = {k: vars(args_ns)[k] for k in argnames if k in args_ns}
            kwargs = {k: v for k, v in kwargs.items() if v is not None}
            self.replay_custom_record(args_ns.NAME, **kwargs)
