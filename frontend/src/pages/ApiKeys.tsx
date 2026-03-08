import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, InputNumber, message, Tag, Popconfirm, Space, Typography } from 'antd'
import { KeyOutlined, DeleteOutlined, StopOutlined, ReloadOutlined } from '@ant-design/icons'
import { apiKeysApi } from '../api'
import type { ColumnsType } from 'antd/es/table'

const { Title } = Typography

interface APIKeyItem {
  id: number
  name: string
  key_prefix: string
  key?: string
  llm_model?: string
  quota_limit: number
  quota_used: number
  is_active: boolean
  created_at: string
  last_used_at?: string
}

export default function ApiKeys() {
  const [loading, setLoading] = useState(false)
  const [keys, setKeys] = useState<APIKeyItem[]>([])
  const [modalVisible, setModalVisible] = useState(false)
  const [newKey, setNewKey] = useState<string | null>(null)
  const [form] = Form.useForm()

  const fetchKeys = async () => {
    setLoading(true)
    try {
      const { data } = await apiKeysApi.list()
      setKeys(data)
    } catch (error) {
      message.error('获取 API Keys 失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchKeys()
  }, [])

  const handleCreate = async (values: { name: string; quota_limit?: number; llm_model?: string }) => {
    try {
      const { data } = await apiKeysApi.create({
        name: values.name,
        quota_limit: values.quota_limit || 1000,
        llm_model: values.llm_model,
      })
      setNewKey(data.key)
      message.success('API Key 创建成功')
      fetchKeys()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await apiKeysApi.delete(id)
      message.success('删除成功')
      fetchKeys()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleDeactivate = async (id: number) => {
    try {
      await apiKeysApi.deactivate(id)
      message.success('已停用')
      fetchKeys()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleResetQuota = async (id: number) => {
    try {
      await apiKeysApi.resetQuota(id)
      message.success('配额已重置')
      fetchKeys()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const columns: ColumnsType<APIKeyItem> = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: 'Key 前缀', dataIndex: 'key_prefix', key: 'key_prefix' },
    { title: '模型', dataIndex: 'llm_model', key: 'llm_model', render: (v) => v || '-' },
    {
      title: '配额',
      key: 'quota',
      render: (_, record) => `${record.quota_used} / ${record.quota_limit}`,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (v) => v ? <Tag color="green">启用</Tag> : <Tag color="red">停用</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<ReloadOutlined />} onClick={() => handleResetQuota(record.id)}>
            重置配额
          </Button>
          {record.is_active && (
            <Button size="small" icon={<StopOutlined />} onClick={() => handleDeactivate(record.id)}>
              停用
            </Button>
          )}
          <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4}>API Keys</Title>
        <Button type="primary" icon={<KeyOutlined />} onClick={() => setModalVisible(true)}>
          创建 API Key
        </Button>
      </div>

      <Table columns={columns} dataSource={keys} rowKey="id" loading={loading} />

      <Modal
        title="创建 API Key"
        open={modalVisible}
        onCancel={() => { setModalVisible(false); form.resetFields(); setNewKey(null); }}
        onOk={() => form.submit()}
        okText="创建"
      >
        {newKey ? (
          <div>
            <p style={{ color: '#ff4d4f', marginBottom: 8 }}>请保存您的 API Key，它只显示一次：</p>
            <Input.TextArea value={newKey} rows={3} readOnly />
          </div>
        ) : (
          <Form form={form} layout="vertical" onFinish={handleCreate}>
            <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
              <Input placeholder="例如：开发环境" />
            </Form.Item>
            <Form.Item name="quota_limit" label="配额限制" initialValue={1000}>
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="llm_model" label="LLM 模型（可选）">
              <Input placeholder="例如：z-ai/glm-5" />
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  )
}
