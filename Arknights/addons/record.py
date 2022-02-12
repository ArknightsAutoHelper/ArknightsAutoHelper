import os
import re
import json
import imgreco.imgops

from automator import AddonBase, cli_command
import app
from .common import CommonAddon

record_basedir = app.writable_root.joinpath('custom_record')

class RecordAddon(AddonBase):
    def create_custom_record(self, record_name, roi_size=64, wait_seconds_after_touch=1,
                             description='', back_to_main=True, prefer_mode='match_template', threshold=0.7):
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
        self.logger.info('滑动屏幕以退出录制.')
        self.logger.info('开始录制, 请点击相关区域...')
        sock = self.device.device_session_factory().shell_stream('getevent')
        f = sock.makefile('rb')
        while True:
            x = 0
            y = 0
            point_list = []
            touch_down = False
            screen = self.device.screenshot()
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
                    # todo 处理屏幕滑动
                    continue
        with open(record_dir.joinpath('record.json'), 'w', encoding='utf-8') as f:
            json.dump(record_data, f, ensure_ascii=False, indent=4, sort_keys=True)

    def get_record_path(self, record_name):
        record_dir = record_basedir.joinpath(record_name)
        if not record_dir.exists():
            return None
        return record_dir

    def replay_custom_record(self, record_name, mode=None, back_to_main=None):
        from util import cvimage as Image
        record_dir = self.get_record_path(record_name)
        if record_dir is None:
            self.logger.error(f'未找到相应的记录: {record_name}')
            raise RuntimeError(f'未找到相应的记录: {record_name}')

        with open(record_dir.joinpath('record.json'), 'r', encoding='utf-8') as f:
            record_data = json.load(f)
        self.logger.info(f'record description: {record_data.get("description")}')
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
        x, y = 0, 0
        for record in records:
            if record['type'] == 'tap':
                repeat = record.get('repeat', 1)
                raise_exception = record.get('raise_exception', True)
                threshold = record.get('threshold', 0.7)
                for _ in range(repeat):
                    if mode == 'match_template':
                        screen = self.device.screenshot()
                        gray_screen = screen.convert('L')
                        if ratio != 1:
                            gray_screen = gray_screen.resize((int(self.viewport[0] * ratio), record_height))
                        template = Image.open(record_dir.joinpath(record['img'])).convert('L')
                        (x, y), r = imgreco.imgops.match_template(gray_screen, template)
                        x = x // ratio
                        y = y // ratio
                        self.logger.info(f'(x, y), r, record: {(x, y), r, record}')
                        if r < threshold:
                            if raise_exception:
                                self.logger.error('无法识别的图像: ' + record['img'])
                                raise RuntimeError('无法识别的图像: ' + record['img'])
                            break
                    elif mode == 'point':
                        # 这个模式屏幕尺寸宽高比必须与记录中的保持一至
                        assert record_data['screen_width'] == int(self.viewport[0] * ratio)
                        x, y = record['point']
                        x = x // ratio
                        y = y // ratio
                    self.device.touch_tap((x, y), offsets=(5, 5))
                    if record.get('wait_seconds_after_touch'):
                        self.delay(record['wait_seconds_after_touch'])

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
            self.create_custom_record(args_ns.NAME, **kwargs)
        elif subcommand == 'play':
            argnames = ['back_to_main', 'mode']
            kwargs = {k: vars(args_ns)[k] for k in argnames if k in args_ns}
            self.replay_custom_record(args_ns.NAME, **kwargs)
