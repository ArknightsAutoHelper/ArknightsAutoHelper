desc = """
请先在 config.yaml 中配置以下参数:

addons:
  activity:
    # 需要刷的关卡
    stage: SV-9
    # 重复次数
    repeat_times: 1000

"""

if __name__ == '__main__':
    import config
    from addons.activity import ActivityAddOn
    try:
        stage = config.get('addons/activity/stage')
        repeat_times = config.get('addons/activity/repeat_times', 1000)
        addon = ActivityAddOn()
        addon.run(stage, repeat_times)
    except KeyError as e:
        print(desc)
        exit(0)
