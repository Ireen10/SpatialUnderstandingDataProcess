import React from 'react';
import { Input, InputNumber, Select, Switch, Slider } from 'antd';

interface Parameter {
  name: string;
  type: string;
  default?: any;
  description?: string;
  required?: boolean;
  options?: string[];
}

interface ModuleParamsFormProps {
  parameters: Parameter[];
  values: Record<string, any>;
  onChange: (values: Record<string, any>) => void;
}

export const ModuleParamsForm: React.FC<ModuleParamsFormProps> = ({ parameters = [], values = {}, onChange }) => {
  const renderControl = (param: Parameter) => {
    const value = values[param.name] !== undefined ? values[param.name] : param.default;

    if (param.options) {
      return (
        <Select
          value={value}
          onChange={(val) => onChange({ ...values, [param.name]: val })}
          style={{ width: '100%' }}
        >
          {param.options.map((opt) => (
            <Select.Option key={opt} value={opt}>{opt}</Select.Option>
          ))}
        </Select>
      );
    }

    if (param.type === 'boolean') {
      return (
        <Switch
          checked={!!value}
          onChange={(checked) => onChange({ ...values, [param.name]: checked })}
        />
      );
    }

    if (['number', 'int', 'float'].includes(param.type)) {
      return (
        <InputNumber
          value={typeof value === 'number' ? value : 0}
          onChange={(val) => onChange({ ...values, [param.name]: val })}
          style={{ width: '100%' }}
        />
      );
    }

    return (
      <Input
        value={typeof value === 'string' ? value : ''}
        onChange={(e) => onChange({ ...values, [param.name]: e.target.value })}
      />
    );
  };

  if (!parameters || parameters.length === 0) {
    return <div style={{ color: '#999', padding: '16px' }}>该模块没有可配置参数</div>;
  }

  return (
    <div>
      {parameters.map((param, idx) => (
        <div key={idx} style={{ marginBottom: '12px' }}>
          <div style={{ fontSize: '13px', marginBottom: '4px' }}>
            <strong>{param.name}</strong>
            {param.required && <span style={{ color: 'red', marginLeft: '4px' }}>*</span>}
          </div>
          {param.description && (
            <div style={{ fontSize: '11px', color: '#999', marginBottom: '4px' }}>{param.description}</div>
          )}
          {renderControl(param)}
        </div>
      ))}
    </div>
  );
};

export default ModuleParamsForm;
