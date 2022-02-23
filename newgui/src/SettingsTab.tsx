import schema from './schema_viewmodel.json';

import { FieldView, SchemaView, SchemaTitle, PopulateAtomFromSchema } from './DynamicSettings';
import { Box, Flex } from '@chakra-ui/layout';
import { Button, ButtonGroup, Card, Text, Divider, Switch, InputGroup, NumericInput } from '@blueprintjs/core';
import React, { useCallback, useMemo, useState } from 'react';
import { DrakModePreference, updateDarkMode } from './darkmode';
import { useLocalStorage } from './LocalStorageHook';

import * as globalState from './AppGlobalState'
import { Field } from './SchemaViewModel';

const ThemeSettings = React.memo(() => {
  const [colorScheme, setColorScheme] = globalState.colorScheme.useState();
  return (
    <Flex flexDirection="row" alignItems="center" width="100%" className="dynamic-setting-field">
      <div className="flex-grow-1">主题</div>
      <ButtonGroup>
        <Button active={colorScheme === 'system'} onClick={() => setColorScheme('system')}>跟随系统</Button>
        <Button active={colorScheme === 'light'} onClick={() => setColorScheme('light')} icon="flash">亮色</Button>
        <Button active={colorScheme === 'dark'} onClick={() => setColorScheme('dark')} icon="moon">暗色</Button>
      </ButtonGroup>
    </Flex>
  )
});

const checkUpdateField: Field = {
  field_type: 'Field',
  value_type: 'bool',
  value: false,
  local_name: 'check_update',
  full_name: 'gui.check_update',
  title: '启动时检查更新',
};
const logScrollbackField: Field = {
  field_type: 'Field',
  value_type: 'int',
  value: 1000,
  min: 100,
  max: 5000,
  local_name: 'log_scrollback',
  full_name: 'gui.log_scrollback',
  title: '历史日志行数',
  doc: '在 GUI 中保留过多历史日志可能影响性能，完整日志可以在日志文件中查看。',
};

function GuiSettings() {
  // const [autoUpdate, setAutoUpdate] = globalState.autoUpdate.useState();
  const [logScrollbackLimit, setLogScrollbackLimit] = globalState.logScrollbackLimit.useState();
  // const [newLogScrollbackLimit, setNewLogScrollbackLimit] = useState(logScrollbackLimit);

  // const handleToggleButton = (value) => {
  //   setNewLogScrollbackLimit(value);
  //   setLogScrollbackLimit(value);
  // };
  return (
    <div className="width-100 dynamic-setting-namespace">
      <SchemaTitle title="GUI 设置" description="立即生效" />
      <div className="dynamic-setting-namespace dynamic-setting-namespace-indent">
        <Divider className="dynamic-setting-divider" />
        <ThemeSettings />
        <Divider className="dynamic-setting-divider" />
        {/* <Flex flexDirection="row" alignItems="center" width="100%" className="dynamic-setting-field">
          <Text>启动时检查更新</Text>
          <Box flexGrow={1}/>
          <Switch checked={autoUpdate} onChange={(e: any) => setAutoUpdate(e.target.checked)} />
        </Flex> */}
        <FieldView field={checkUpdateField} valueAtom={globalState.autoUpdate} />
        <Divider className="dynamic-setting-divider" />
        <FieldView field={logScrollbackField} valueAtom={globalState.logScrollbackLimit} />
        <Divider className="dynamic-setting-divider" />
        {/* <Flex flexDirection="row" alignItems="center" width="100%" wrap="wrap" className="dynamic-setting-field" >
          <Text>历史日志行数</Text>
          <Box flexGrow={1}/>
          <NumericInput value={newLogScrollbackLimit} onValueChange={(value) => setNewLogScrollbackLimit(value)} onBlur={() => setLogScrollbackLimit(newLogScrollbackLimit)} onButtonClick={handleToggleButton} max={5000} min={100} minorStepSize={1} stepSize={10} majorStepSize={100} clampValueOnBlur/>
          <Box flexBasis="100%"/>
          <p className="dynamic-setting-field-doc bp3-text-muted"><small>在 GUI 中保留过多历史日志可能影响性能。</small></p>
        </Flex> */}
      </div>
    </div>
  );
}

export default function SettingsTab() {
  const [changed, setChanged] = React.useState(() => new Map());
  const setValueChanged = React.useCallback((full_name, atom, new_value) => setChanged(changed => new Map(changed).set(full_name, new_value)), []);
  const [atoms, setAtoms] = React.useState(() => PopulateAtomFromSchema(schema as any, setValueChanged));

  const handleDiscard = useCallback(() => {
    setChanged(new Map());
    setAtoms(() => PopulateAtomFromSchema(schema as any, setValueChanged));
  }, [setValueChanged]);
  const changedSize = changed.size;
  const handleSave = useCallback(() => {
    console.log(changed);
  }, [changed]);

  return (
    <Box width="100%" height="100%" flexGrow={1} minHeight="0" position="relative" className="overflow-y-auto">
      {/*
    https://bugzilla.mozilla.org/show_bug.cgi?id=1488080
    https://bugzilla.mozilla.org/show_bug.cgi?id=1377072
    */}
      {useMemo(() =>
        <Flex flexDirection="column" alignItems="center" margin="0 auto" padding="8px" maxWidth="640px" className='bp3-card square-card' >
          <GuiSettings />
          <SchemaView namespaceName='config.yaml' schema={schema as any} showFieldName valueAtoms={atoms} />
          <Box flexGrow={1} flexShrink={0} paddingTop={0}></Box>
        </Flex>, [atoms])}

      {useMemo(() =>
        <Box position="sticky" bottom="0" visibility={changedSize > 0 ? null : 'hidden'} className="bp3-card square-card bp3-elevation-2" padding="1em">
          <Flex justifyContent="flex-end" alignItems="center" gap="1em">
            <Text>已更改 {changedSize} 项</Text>
            <Button icon="trash" intent="danger" onClick={handleDiscard}>放弃</Button>
            <Button icon="floppy-disk" intent="success" onClick={handleSave}>保存</Button>
          </Flex>
        </Box>, [changedSize, handleDiscard, handleSave])}

    </Box>

  );
}
