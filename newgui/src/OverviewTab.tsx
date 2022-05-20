import { Flex, Box } from '@chakra-ui/layout'
import * as React from 'react';
import { Button, Card, Divider, H5, Icon, MenuItem, Switch, Text } from '@blueprintjs/core';
import { Select } from "@blueprintjs/select";
import TaskScheduler from './TaskScheduler';
import "./OverviewTab.scss";

import * as globalState from './AppGlobalState';
import { ILogFrame } from './ILogFrame';
import { activeColorScheme } from './darkmode';

interface IDeviceSelect {
  key: string;
  display: string;
}

const DeviceSelect = Select.ofType<IDeviceSelect>();


let trollCount = 1;

const LogRecord = React.memo(({ level, time, message }: any) => {
  return (
    <tr className='log-record' data-loglevel={level}>
      <td className='log-record-field no-wrap text-align-right time-field' width="5.5em">{time}</td>
      <td className='log-record-field text-align-right level-field' width="4em">{level}</td>
      <td className='log-record-field message-field'>{message}</td>
    </tr>
  )
});

function LogPanel({ autoScroll, showDebugMessage }) {
  const logFrame = React.useRef<HTMLIFrameElement>(null);
  const [logs, setLogs] = React.useState([]);
  // const [limit] = globalState.logScrollbackLimit.useState();
  const lastlog = logs[logs.length - 1]?.id;
  React.useEffect(() => {
    const subscription = globalState.log$.asObservable().subscribe(log => {
      (logFrame.current?.contentWindow as ILogFrame)?.addLogRecord?.(log);
    });
    const sub2 = globalState.logScrollbackLimit.asObservable().subscribe(limit => {
        (logFrame.current?.contentWindow as ILogFrame)?.setScrollBackLimit?.(limit);
    });
    const sub3 = activeColorScheme.asObservable().subscribe(colorScheme => {
      (logFrame.current?.contentWindow as ILogFrame)?.setDarkMode?.(colorScheme === 'dark');
    });
    return () => {
      subscription.unsubscribe();
      sub2.unsubscribe();
      sub3.unsubscribe();
    };
  }, [logFrame]);
  React.useEffect(() => {
    (logFrame.current?.contentWindow as ILogFrame)?.setAutoScroll?.(autoScroll);
  }, [logFrame, autoScroll]);
  React.useEffect(() => {
    (logFrame.current?.contentWindow as ILogFrame)?.setShowDebug?.(showDebugMessage);
  }, [logFrame, showDebugMessage]);

  const onLoad = React.useCallback(() => {
    (logFrame.current?.contentWindow as ILogFrame)?.setScrollBackLimit?.(globalState.logScrollbackLimit.getValue());
    (logFrame.current?.contentWindow as ILogFrame)?.setDarkMode?.(activeColorScheme.getValue() === 'dark');
    (logFrame.current?.contentWindow as ILogFrame)?.setAutoScroll?.(autoScroll);
    (logFrame.current?.contentWindow as ILogFrame)?.setShowDebug?.(showDebugMessage);
  }, [logFrame]);
  return React.useMemo(() => (
        <iframe ref={logFrame} className='log-frame flex-grow-1 min-height-0 default-background' src="log-frame.html" title="log-frame" onLoad={onLoad}></iframe>
    ), []);
}


export default function OverviewTab() {
  const [autoScroll, setAutoScroll] = React.useState(true);
  const [showDebugMessage, setShowDebugMessage] = React.useState(false);
  const [currentDevice] = globalState.currentDevice.useState();
  const [clearTag, setClearTag] = React.useState(() => new Date().toISOString());
  const addLog = () => {
    const level = ['DEBUG', 'INFO', 'WARNING', 'ERROR'][Math.floor(Math.random() * 4)];
    globalState.log$.next({ level, time: new Date(), message: "Hello world! " + trollCount, id: +new Date() + Math.random().toString() })
    trollCount++;
  };

  const batchFlood = () => {
    for (let i = 0; i < 100; i++) {
      addLog();
    }
  };

  const asyncFlood = () => {
    const worker = (i: number) => {
      addLog();
      if (i < 100) {
        setTimeout(() => worker(i + 1), 0);
      }
    }
    setTimeout(() => worker(1), 0);
  };

  return (
    <Flex flexDirection="row" alignItems="stretch" height="100%" className="card-background">
      <Flex flexDirection="column" width={280} height="100%" alignItems="stretch" className="pane left">
        <Box className="pane top" padding="12px" >
        <H5>
          <Flex flexDirection="row" alignItems={'center'}>
            <Icon icon="link" style={{ marginRight: "0.5em" }} /><Text>连接设备</Text>
          </Flex>
        </H5>
        <DeviceSelect fill={true} items={[{ key: '1', display: '127.0.0.1:5555' }, { key: '2', display: '127.0.0.1:7555' }]} itemRenderer={x => <MenuItem text={x.display} key={x.key} />} onItemSelect={(x) => { }} popoverProps={{ minimal: true, usePortal: false }} filterable={false} matchTargetWidth={true}>
          <Button fill={true} text={currentDevice === null ? '(auto)' : currentDevice} rightIcon="caret-down" alignText='left' />
        </DeviceSelect>
        </Box>
        
        <Flex flexDirection="column" padding="12px" flexGrow={1}>
          <H5>
            <Flex flexDirection="row" alignItems={'center'}>
              <Icon icon="property" style={{ marginRight: "0.5em" }} /><Text>任务队列</Text>
            </Flex>
          </H5>

          {React.useMemo(() => <TaskScheduler />, [])}
        </Flex>



      </Flex>
      <Flex flexDirection="column" flexGrow={1} width="0" height="100%" style={{ position: 'relative' }}>
        <Flex className="top pane" alignItems={'center'} padding="8px 12px" >
          <H5 style={{margin: 0}}>
            <Flex flexDirection="row" alignItems={'center'}>
              <Icon icon="console" style={{ marginRight: "0.5em" }} /><Text>运行日志</Text>
            </Flex>
          </H5>
          <Box flexGrow={1} />
          <Button onClick={() => { setClearTag(new Date().toISOString()); trollCount = 0; }}>clear log</Button>
          <Button onClick={batchFlood}>batch flood log</Button>
          <Button onClick={asyncFlood}>async flood log</Button>
          <Button onClick={addLog}>add log</Button>
          <Switch checked={showDebugMessage} onChange={(e) => setShowDebugMessage((e.target as any).checked)} label="显示调试信息" className="no-bottom-margin" />
          <Divider style={{ alignSelf: 'stretch' }} />
          <Switch checked={autoScroll} onChange={(e) => setAutoScroll((e.target as any).checked)} label="自动滚动" className="no-bottom-margin" />
        </Flex>
        <LogPanel key={clearTag} autoScroll={autoScroll} showDebugMessage={showDebugMessage} />
      </Flex>
    </Flex>
  )
}