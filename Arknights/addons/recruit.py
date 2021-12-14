from automator import AddonBase
class RecruitAddon(AddonBase):
    def on_attach(self) -> None:
        self.register_cli_command('recruit', self.cli_recruit, self.cli_recruit.__doc__)

    def recruit(self):
        import imgreco.recruit
        from . import recruit_calc
        self.logger.info('识别招募标签')
        tags = imgreco.recruit.get_recruit_tags(self.device.screenshot())
        self.logger.info('可选标签：%s', ' '.join(tags))
        result = recruit_calc.calculate(tags)
        self.logger.debug('计算结果：%s', repr(result))
        return result

    def cli_recruit(self, argv):
        """
        recruit [tags ...]
        公开招募识别/计算，不指定标签则从截图中识别
        """
        from . import recruit_calc

        if 2 <= len(argv) <= 6:
            tags = argv[1:]
            result = recruit_calc.calculate(tags)
        elif len(argv) == 1:
            with self.helper.frontend.context:
                result = self.recruit()
        else:
            print('要素过多')
            return 1

        colors = ['\033[36m', '\033[90m', '\033[37m', '\033[32m', '\033[93m', '\033[91m']
        reset = '\033[39m'
        for tags, operators, rank in result:
            taglist = ','.join(tags)
            if rank >= 1:
                taglist = '\033[96m' + taglist + '\033[39m'
            print("%s: %s" % (taglist, ' '.join(colors[op[1]] + op[0] + reset for op in operators)))
