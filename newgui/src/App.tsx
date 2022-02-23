import logo from './carrot.svg';
import {
  Alignment,
  Button,
  Classes,
  Navbar,
  Switch,
  Text,
  Icon,
  Spinner,
  NonIdealState,
  ButtonGroup
} from "@blueprintjs/core";

import { Tooltip2 } from '@blueprintjs/popover2';


import './App.scss';
import './utils.scss';
import { Flex, Box } from '@chakra-ui/layout'
import * as React from 'react';
import OverviewTab from './OverviewTab';
import SettingsTab from './SettingsTab';

import { currentTab, updateAvailiable } from './AppGlobalState' 
import AboutTab from './AboutTab';
import { useLocalStorage } from './LocalStorageHook';
import GalleryTab from './GalleryTab';

import * as globalState from './AppGlobalState';

export function App() {
  const [showAboutOnStartup] = globalState.showAboutOnStartup.useState();

  const [currentTab, setActiveTab] = globalState.currentTab.useState();
  const activeTab = currentTab || (showAboutOnStartup ? 'about' : 'overview');
  const [hasUpdate] = globalState.updateAvailiable.useState();
  const [ loading, setLoading ] = React.useState(false);
  const defaultClasses = "tab-container overflow-y-auto min-height-0";
    return (
      <Flex flexDirection="column" alignItems="stretch" height="100%" className="app">
        <Navbar className='app-titlebar'>
          <Navbar.Group align={Alignment.LEFT} className='app-titlebar-left-padding'/>
          <Navbar.Group align={Alignment.LEFT}>
            <Navbar.Heading><img className='app-icon' src={logo} width="24" height="24"/></Navbar.Heading>
            <ButtonGroup className='app-titlebar-controls'>
              <Button active={activeTab === 'overview'} onPointerDown={() => setActiveTab('overview')} icon="dashboard" text="总览" />
              <Button active={activeTab === 'gallery'} onPointerDown={() => setActiveTab('gallery')} icon="control" text="任务库" />
              <Button active={activeTab === 'statistics'} onPointerDown={() => setActiveTab('statistics')} icon="timeline-bar-chart" text="统计" />
              <Button active={activeTab === 'settings'} onPointerDown={() => setActiveTab('settings')} icon="cog" text="设置" />
            </ButtonGroup>
            <Box flexGrow={1}/>
          </Navbar.Group>
          <Navbar.Group align={Alignment.RIGHT} className='app-titlebar-right-padding'/>
          <Navbar.Group align={Alignment.RIGHT} className='app-titlebar-controls'>
            <Tooltip2 content="发现新版本" placement='bottom' disabled={!hasUpdate} >
              <Button minimal intent={hasUpdate ? 'success' : null} active={activeTab === 'about'} onPointerDown={() => setActiveTab('about')} icon="info-sign"  />
            </Tooltip2>
          </Navbar.Group>
        </Navbar>
        <Box flexGrow={1} minHeight="0" position="relative">
          <Box className={defaultClasses + (activeTab !== 'overview' ?  ' inactive' : '')}>
            {React.useMemo(()=><OverviewTab />, [])}
          </Box>
          <Box className={defaultClasses + (activeTab !== 'gallery' ?  ' inactive' : '')}>
            {React.useMemo(()=><GalleryTab />, [])}
          </Box>
          <Box className={defaultClasses + (activeTab !== 'settings' ?  ' inactive' : '')}>
            {React.useMemo(()=><SettingsTab />, [])}
          </Box>
          <Box className={defaultClasses + (activeTab !== 'about' ?  ' inactive' : '')}>
            {React.useMemo(()=><AboutTab />, [])}
          </Box>
        </Box>

        {loading &&
            <Box style={{position: 'absolute', background: "rgba(255,255,255, 0.7)", left: "0", right: "0", top: "0", bottom: "0", zIndex: 9999}}>
              <NonIdealState
                icon={<Spinner />}
                title="Loading…"
              />
            </Box>
          }
      </Flex>
      
    );
}

export default App;
