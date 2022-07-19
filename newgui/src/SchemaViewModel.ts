interface BaseField {
    field_type: string;
    local_name: string;
    full_name: string;
    title: string;
    doc?: string;
}


interface ValueField<TType extends string, TValue extends unknown> extends BaseField {
    field_type: "Field";
    value_type: TType;
    value: TValue;
}

type BooleanField = ValueField<"bool", boolean>;

interface IntegerField extends ValueField<"int", number> {
    min?: number;
    max?: number;
}

type StringField = ValueField<"str", string>;

interface EnumField extends BaseField {
    field_type: "EnumField";
    enum_values: string[];
    value: string;
}

interface ListField extends BaseField {
    field_type: "ListField";
    element_type: string;
    value: string[];
}

type UnknwonValueField = ValueField<string, unknown>;

interface Namespace extends BaseField {
    field_type: "Namespace";
    fields: Field[];
}

export type Field = IntegerField | BooleanField | StringField | EnumField | ListField | Namespace;

export interface SchemaViewModel {
    name?: string;
    description?: string;
    fields: Field[];
};

function testaaaaa(x: Field) {
    if (x.field_type === 'Field') {
        if (x.value_type === 'str') {
            x
        }
    }
    else if (x.field_type === 'EnumField') {
        console.log(x.enum_values);
        console.log(x.value);
    }
    else if (x.field_type === 'ListField') {
        console.log(x.element_type);
        console.log(x.value);
    }
}
