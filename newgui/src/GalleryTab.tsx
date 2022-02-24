import { Tree, TreeNodeInfo } from "@blueprintjs/core";
import { Box, Flex } from "@chakra-ui/layout";


const treeData: TreeNodeInfo[] = [
  {id: '0', label: '登录游戏', isExpanded: true, childNodes: [
    {id: '0.1', label: '启动模拟器'}
  ]},
  {id: '1', label: '代理指挥作战', isExpanded: true, childNodes: [
    {id: '1.1', label: '刷图计划'},
    {id: '1.2', label: '一键长草'},
    {id: '1.3', label: '补充芯片库存'},
  ]},
  {id: '2', label: '日常任务', isExpanded: true, childNodes: [
    {id: '2.1', label: '收取邮件'},
    {id: '2.2', label: '信用商店'},
    {id: '2.3', label: '公开招募'},
    {id: '2.3', label: '好友查房'},
    {id: '2.4', label: '领取任务奖励'},
  ]},
  {id: '3', label: '基建', isExpanded: true, childNodes: [
    {id: '3.1', label: '基建收取'},
    {id: '3.2', label: '线索交流'},
    {id: '3.3', label: '自动换班'},
  ]},
  {id: '4', label: '操作录制', isExpanded: true, childNodes: [
    {id: '4.1', label: '录制'},
  ]},
  {id: '5', label: '工具', isExpanded: true, childNodes: [
    {id: '5.1', label: '测试设备连接'},
  ]},
] 

export default function GalleryTab() {
  return (
    <Flex width="100%" height="100%" flexGrow={1} flexDirection='row' alignItems='stretch' minHeight={0}>
      <Box width="200px" height="100%" minHeight="0" padding="0" className="bp3-card square-card overflow-y-auto">
        <Tree contents={treeData}></Tree>
      </Box>
    </Flex>
  )
}
