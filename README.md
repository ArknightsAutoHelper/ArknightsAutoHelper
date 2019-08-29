# Arknghts Auto Helper

### 关于这个 dev 分支

Prurite 对于 ArknightsAutoHelper 的 base.py 的一些重构，目标是优化代码，将现有的点击方式（中心点偏移）换为范围内随机，并加入作战完成后自动收取每日任务奖励的功能。也许还能再顺手提升一下可扩展性？

### Todolist

[ ] 重构 base.py 的代码，整理变量名
  [x] 整理了已重构部分的变量名
  [x] 前半段**（没有经过测试，不保证没有bug）**
  [ ] __check_current_san
  [ ] __check_curreng_san_debug
  [ ] check_curreng_san
  [ ] battle_selector
[ ] 将点击操作换为范围操作
  [x] 更新点击函数（现在请使用 Arknights_helper.mouse_click 函数来点击一个按钮）
  [ ] 更新 click_location 中的参数
[ ] 加入收获每日任务功能