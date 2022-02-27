import { Button, H4, Icon, Switch } from "@blueprintjs/core";
import { Box, Flex } from "@chakra-ui/layout";

import * as globalState from "./AppGlobalState";

export default function AboutTab() {
  const [showOnStartup, setShowOnStartup] = globalState.showAboutOnStartup.useState();

  return (
    <Box width="100%" height="100%"  flexGrow={1} flexDirection='column' alignItems='center' minHeight={0} className="overflow-y-auto">
      <Box maxWidth={640} minHeight="100%" height="auto" margin="0 auto" className='bp3-card square-card'>
        <H4>Arknights Auto Helper</H4>
        <p className='bp3-text-muted'>版本 <span className="user-select-text">{process.env.REACT_APP_VERSION || "UNKNOWN"}</span></p>
        <Box style={{clear: 'both'}} ><br/></Box>

        <p className='bp3-running-text'>Arknights Auto Helper 是开源软件（<a href="https://github.com/ninthDevilHAUNSTER/ArknightsAutoHelper" target='_blank' rel='noreferrer'>项目主页 <Icon size={12} htmlTitle="在新窗口中打开" style={{verticalAlign: 'baseline'}} icon="share"/></a>），如果您为获取本软件付出了额外的经济成本，则可能是第三方向您分发时收取的服务费用。原作者无法保证第三方分发版本（可能经过修改）的安全性，亦无法对第三方分发版本提供任何支持，请谨慎甄别。</p>
        <p className='bp3-running-text'>本软件依「原样（as is）」提供，不附带任何形式的担保。对因本软件本身，或使用、分发本软件而产生的任何直接或间接后果，原作者不承担任何责任。请查阅软件安装目录下的「LICENSE」文件。</p>

        <p>
          <Switch inline label='启动时显示此页面' checked={showOnStartup} onChange={(e: any) => setShowOnStartup(e.target.checked)} />
        </p>
        <p>
          <Flex gap='1em'>
            <Button>检查更新</Button>
          </Flex>
        </p>
      </Box>
    </Box>
  )
}
