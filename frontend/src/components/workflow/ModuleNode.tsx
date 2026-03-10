import React, { memo, FC } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Tag, Tooltip } from 'antd';

export type ModuleNodeType = 'input_adapter' | 'processor' | 'data_relay' | 'output_adapter' | 'branch';

interface PortDefinition {
  port: string;
  type: string;
  description?: string;
  required?: boolean;
}

interface ModuleNodeData {
  label: string;
  moduleType: ModuleNodeType;
  description?: string;
  moduleName?: string;
  status?: 'idle' | 'running' | 'success' | 'error';
  inputs?: PortDefinition[];
  outputs?: PortDefinition[];
}

const getIcon = (moduleType: ModuleNodeType): string => {
  switch (moduleType) {
    case 'input_adapter': return '📥';
    case 'processor': return '⚙️';
    case 'data_relay': return '🔀';
    case 'output_adapter': return '📤';
    case 'branch': return '🔷';
    default: return '⚙️';
  }
};

const getColor = (moduleType: ModuleNodeType): string => {
  switch (moduleType) {
    case 'input_adapter': return '#52c41a';
    case 'processor': return '#1890ff';
    case 'data_relay': return '#722ed1';
    case 'output_adapter': return '#13c2c2';
    case 'branch': return '#fa8c16';
    default: return '#666';
  }
};

const ModuleNodeComponent: FC<NodeProps<ModuleNodeData>> = ({ data }) => {
  const { label, moduleType, description, moduleName, status, inputs = [], outputs = [] } = data;

  return (
    <div
      style={{
        padding: '12px 16px',
        background: '#fff',
        border: `2px solid ${getColor(moduleType)}`,
        borderRadius: '8px',
        minWidth: '200px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      }}
    >
      {/* 头部 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <span style={{ fontSize: '16px' }}>{getIcon(moduleType)}</span>
        <strong style={{ fontSize: '14px' }}>{label}</strong>
        {status && (
          <Tag color={status === 'error' ? 'red' : status === 'success' ? 'green' : 'default'} style={{ marginLeft: 'auto' }}>
            {status}
          </Tag>
        )}
      </div>

      {/* 描述 */}
      {description && (
        <div style={{ fontSize: '12px', color: '#666', marginBottom: '12px' }}>
          <Tooltip title={description}>
            {description.length > 50 ? description.substring(0, 50) + '...' : description}
          </Tooltip>
        </div>
      )}

      {/* 输入端口 */}
      {inputs?.length > 0 && inputs.map((input, idx) => (
        <div key={idx} style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
          <Handle type="target" position={Position.Left} id={input.port} style={{ background: getColor(moduleType), width: '8px', height: '8px' }} />
          <span style={{ fontSize: '11px', marginLeft: '12px' }}>{input.port}</span>
          <Tag color="blue" style={{ fontSize: '9px', marginLeft: '4px' }}>{input.type}</Tag>
        </div>
      ))}

      {/* 输出端口 */}
      {outputs?.length > 0 && outputs.map((output, idx) => (
        <div key={idx} style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
          <Handle type="source" position={Position.Right} id={output.port} style={{ background: getColor(moduleType), width: '8px', height: '8px' }} />
          <span style={{ fontSize: '11px', marginLeft: '12px' }}>{output.port}</span>
          <Tag color="green" style={{ fontSize: '9px', marginLeft: '4px' }}>{output.type}</Tag>
        </div>
      ))}
    </div>
  );
};

export const ModuleNode = memo(ModuleNodeComponent);
