import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Modal, message } from 'antd';
import { PlayCircleOutlined, DeleteOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import axios from 'axios';

interface FlowMeta {
  flow_id: string;
  name: string;
  created_at?: string;
  updated_at?: string;
}

interface FlowListProps {
  onLoadFlow?: (flow: any) => void;
  onExecuteFlow?: (flow: any) => void;
}

export const FlowList: React.FC<FlowListProps> = ({ onLoadFlow, onExecuteFlow }) => {
  const [flows, setFlows] = useState<FlowMeta[]>([]);
  const [loading, setLoading] = useState(false);

  const loadFlows = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/v1/flows/list');
      setFlows(response.data.flows);
    } catch (error: any) {
      message.error(`加载流程列表失败：${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadFlows(); }, []);

  const handleDelete = async (flowId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除流程 "${flowId}" 吗？`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await axios.delete(`/api/v1/flows/${flowId}`);
          message.success('流程已删除');
          loadFlows();
        } catch (error: any) {
          message.error(`删除失败：${error.message}`);
        }
      },
    });
  };

  const columns = [
    { title: '流程 ID', dataIndex: 'flow_id', key: 'flow_id' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: FlowMeta) => (
        <Space size="small">
          <Button type="link" size="small" onClick={() => onLoadFlow && onLoadFlow({ flow_id: record.flow_id })}>加载</Button>
          <Button type="link" size="small" icon={<PlayCircleOutlined />} onClick={() => onExecuteFlow && onExecuteFlow({ flow_id: record.flow_id })}>执行</Button>
          <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.flow_id)}>删除</Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>流程列表</h2>
        <Button icon={<ReloadOutlined />} onClick={loadFlows} loading={loading}>刷新</Button>
      </div>
      <Table columns={columns} dataSource={flows} rowKey="flow_id" loading={loading} pagination={{ pageSize: 20 }} />
    </div>
  );
};

export default FlowList;
