import { Flex, Box } from '@chakra-ui/layout'
import * as React from 'react';
import { Button, Card, Divider, H5, Icon, MenuItem, Switch, Text } from '@blueprintjs/core';
import { Select } from "@blueprintjs/select";
import TaskScheduler from './TaskScheduler';
import "./OverviewTab.scss";

import * as globalState from './AppGlobalState';

interface IDeviceSelect {
  key: string;
  display: string;
}

const DeviceSelect = Select.ofType<IDeviceSelect>();


let trollCount = 1;

const LogRecord = React.memo(({ level, time, message }: any) => {
  return (
    <Box className='log-record' as="tr" data-loglevel={level}>
      <Box className='log-record-field no-wrap text-align-right time-field' width="5.5em" as="td">{time}</Box>
      <Box className='log-record-field text-align-right level-field' width="4em" as="td">{level}</Box>
      <Box className='log-record-field message-field' as="td">{message}</Box>
    </Box>
  )
});

function LogPanel({ autoScroll, showDebugMessage }) {
  const scrollContainer = React.useRef<HTMLDivElement>(null);
  const [logs, setLogs] = React.useState([]);
  // const [limit] = globalState.logScrollbackLimit.useState();
  const lastlog = logs[logs.length - 1]?.id;
  React.useEffect(() => {
    const subscription = globalState.log$.asObservable().subscribe(log => {
      const limit = globalState.logScrollbackLimit.getValue();
      console.log("limit=", limit);
      setLogs(logs => [...logs.slice(-limit + 1), log]);
    });
    return () => subscription.unsubscribe();
  }, []);
  React.useEffect(() => {
    if (autoScroll) {
      window.requestAnimationFrame(() => {
        const elm = scrollContainer.current;
        if (elm) {
          elm.scrollTop = elm.scrollHeight;
        }
      });
    }
  }, [lastlog, autoScroll]);

  return (
    <Card className='card-no-padding flex-grow-1 min-height-0 user-select-text default-background'>
      <Box ref={scrollContainer} className="overflow-y-scroll min-height-0" width="100%" height="100%" >
        <Box className={"log-container" + (showDebugMessage ? ' show-debug' : '')} width="100%" as="table" >
          <tbody>{logs.map((x, i) => <LogRecord {...x} key={x.id} />)}</tbody>
        </Box>
      </Box>
    </Card>
  );
}


export default function OverviewTab() {
  const [autoScroll, setAutoScroll] = React.useState(true);
  const [showDebugMessage, setShowDebugMessage] = React.useState(false);
  const [currentDevice] = globalState.currentDevice.useState();
  const [clearTag, setClearTag] = React.useState(() => new Date().toISOString());
  const addLog = () => {
    const level = ['DEBUG', 'INFO', 'WARNING', 'ERROR'][Math.floor(Math.random() * 4)];
    globalState.log$.next({ level, time: new Date().toISOString().substring(11, 23), message: "Hello world! " + trollCount, id: +new Date() + Math.random().toString() })
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
      <Flex flexDirection="column" width={280} height="100%" alignItems="stretch" style={{ gap: "8px" }} padding="12px" className="bp3-card square-card">
        <H5>
          <Flex flexDirection="row" alignItems={'center'}>
            <Icon icon="link" style={{ marginRight: "0.5em" }} /><Text>连接设备</Text>
          </Flex>
        </H5>
        <DeviceSelect fill={true} items={[{ key: '1', display: '127.0.0.1:5555' }, { key: '2', display: '127.0.0.1:7555' }]} itemRenderer={x => <MenuItem text={x.display} key={x.key} />} onItemSelect={(x) => { }} popoverProps={{ minimal: true, usePortal: false }} filterable={false} matchTargetWidth={true}>
          <Button fill={true} text={currentDevice === null ? '(auto)' : currentDevice} rightIcon="caret-down" alignText='left' />
        </DeviceSelect>

        <Divider />

        <H5>
          <Flex flexDirection="row" alignItems={'center'}>
            <Icon icon="property" style={{ marginRight: "0.5em" }} /><Text>任务队列</Text>
          </Flex>
        </H5>

        {React.useMemo(() => <TaskScheduler />, [])}

      </Flex>
      <Flex flexDirection="column" flexGrow={1} width="0" height="100%" padding="12px" style={{ position: 'relative' }}>
        <Flex alignItems={'center'}>
          <H5>
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