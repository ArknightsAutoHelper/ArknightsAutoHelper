import { Field, SchemaViewModel } from "./SchemaViewModel";

import { H3, H4, H5, H6, HTMLSelect, InputGroup, NumericInput, Switch, TagInput, Divider, Text, Code } from "@blueprintjs/core";
import { Box, Flex } from "@chakra-ui/layout";

import "./DynamicSettings.scss";
import React, { useMemo } from "react";
import { RxAtom } from "./RxAtom";

function LevelingHeader({ nestingLevel, ...props }): ReturnType<typeof H3> {
  switch (nestingLevel) {
    case 1: return <H4 {...props} />;
    case 2: return <H5 {...props} />;
    case 3: return <H6 {...props} />;
    default: return nestingLevel > 3 ? <H6 {...props} /> : <H3 {...props} />;
  }
}

interface ISchemaViewProps {
  schema: SchemaViewModel;
  showFieldName?: boolean;
  namespaceName?: string;
  nestingLevel?: number;
  valueAtoms?: Map<string, RxAtom>;
}

interface IFieldViewProps {
  field: Field;
  showFieldName?: boolean;
  valueOverride?: any;
  valueAtom: RxAtom;
}

export const FieldView = React.memo(({ field, showFieldName, valueAtom }: IFieldViewProps) => {
  let inputElement = null;
  const [value, setValue] = valueAtom.useState();
  const handleChange = e => setValue(e.target.value);
  let display_type = 'inline';
  switch (field.field_type) {
    case "Field":
      switch (field.value_type) {
        case "str":
          inputElement = <><Box flexBasis="100%" height={4} /><InputGroup fill asyncControl value={value} onChange={handleChange} /></>;
          display_type = 'multi_line';
          break;
        case "bool":
          inputElement = <Switch checked={value} onChange={e => setValue((e.target as any).checked)} />;
          break;
        case "int":
          inputElement = <NumericInput value={value} onValueChange={(num, str, elm) => setValue(num)} stepSize={1} majorStepSize={10} minorStepSize={null} min={field.min} max={field.max} clampValueOnBlur />;
          break;
      }
      break;
    case "EnumField":
      inputElement = <HTMLSelect value={value} options={field.enum_values.map(value => ({ value }))} onChange={handleChange} />
      break;
    case "ListField":
      inputElement = <><Box flexBasis="100%" height={4} /><TagInput fill values={value} addOnBlur={true} onChange={(values) => setValue(values)} /></>;
      display_type = 'multi_line';
      break;
  }
  const doc = field.doc;
  const docElement = useMemo(() => doc && (
    <Box flexBasis="100%">
      <p className="dynamic-setting-field-doc bp3-text-muted"><small>{doc}</small></p>
    </Box>
  ), [doc]);

  const { title, local_name } = field;
  const titleElement = useMemo(() => (<>
    <Text>{title || local_name}</Text>
    {showFieldName && title ? <Code style={{ marginInlineStart: "0.5em" }}>{local_name}</Code> : null}
    <Box flexGrow={1} />
  </>), [title, local_name, showFieldName]);

  return (
    <>
      <Flex direction="row" alignItems="baseline" alignContent="center" width="100%" wrap="wrap" className="dynamic-setting-field">
        {titleElement}
        {display_type === 'multi_line' && docElement}
        {inputElement}
        {display_type === 'inline' && docElement}
      </Flex>
      {/* <FormGroup label={field.title || field.local_name} subLabel={field.doc} className="dynamic-setting-field" labelInfo={field.title ? ('(' + field.local_name + ')') : null}>
        {inputElement}
      </FormGroup> */}
    </>
  );
});


export const SchemaTitle = React.memo(({ title, code, description, nestingLevel }: any) => {
  return (<div className={["dynamic-setting-schema-title", "level-" + nestingLevel].join(' ')}>
    <Flex alignItems='baseline'>
      {title && <LevelingHeader nestingLevel={nestingLevel}>{title}</LevelingHeader>}
      {code && <Code style={{ marginInlineStart: "0.5em" }}>{code}</Code>}
    </Flex>
    <p className="dynamic-setting-field-doc bp3-text-muted">{description}</p>
  </div>)
});


function populateFields(fields: Field[], output: Map<string, RxAtom>, onChange?: (full_name: string, atom: RxAtom, newValue) => void) {
  for (const field of fields) {
    if (field.field_type === "Namespace") {
      populateFields(field.value, output, onChange);
    } else if (field.full_name) {
      const newAtom = new RxAtom(field.value)
      if (onChange) newAtom.changed$.subscribe((value) => onChange(field.full_name, newAtom, value));
      output.set(field.full_name, newAtom);
    }
  }
}

export function PopulateAtomFromSchema(schema: SchemaViewModel, onChange?: (full_name: string, atom: RxAtom, newValue) => void): Map<string, RxAtom> {
  const result = new Map<string, RxAtom>();
  populateFields(schema.fields, result, onChange);
  return result;
}

export function SchemaView(props: ISchemaViewProps) {
  let { schema, showFieldName, namespaceName, nestingLevel, valueAtoms } = props;
  nestingLevel = nestingLevel || 0;
  const description = schema.description;
  valueAtoms = valueAtoms || PopulateAtomFromSchema(schema);
  return (
    <div className="dynamic-setting-namespace user-select-text width-100">
      <SchemaTitle title={schema.name} code={showFieldName ? namespaceName : null} {...{ description, nestingLevel }} />
      <Box className={nestingLevel !== 0 ? 'dynamic-setting-namespace-indent': null} >
        {schema.fields.map((field, i, a) => {
          if (field.field_type === 'Field' || field.field_type === 'EnumField' || field.field_type === 'ListField') {
            // text/bool/number input
            const elm = <FieldView key={field.full_name} field={field} showFieldName={showFieldName} valueAtom={valueAtoms.get(field.full_name) || new RxAtom(field.value)} />;
            if (i === 0) {
              return <>
                <Divider className="dynamic-setting-divider"/>
                {elm}
                <Divider className="dynamic-setting-divider"/>
              </>
            } else {
              return <>
                {elm}
                <Divider className="dynamic-setting-divider"/>
              </>
            }
          } else if (field.field_type === 'Namespace') {
            // namespace
            return <SchemaView key={field.full_name} showFieldName={showFieldName} namespaceName={field.local_name} schema={{ name: field.title, description: field.doc, fields: field.value }} nestingLevel={nestingLevel + 1} valueAtoms={valueAtoms} />;
          }
          return null;
        })}
      </Box>
    </div>
  );
}

