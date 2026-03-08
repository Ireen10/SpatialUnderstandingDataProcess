import { useState, useEffect } from 'react'
import { Card, Typography, Form, Input, Button, Select, Divider, message, Space, Alert } from 'antd'
import { SettingOutlined, ApiOutlined, CloudServerOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { initApi } from '../api'

const { Title, Text, Paragraph } = Typography
const { Option } = Select

export default function SetupConfig() {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [config, setConfig] = useState<any>({})
  const [form] = Form.useForm()

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setLoading(true)
    try {
      const res = await initApi.getConfig()
      setConfig(res.data.config || {})
      form.setFieldsValue(res.data.config || {})
    } catch (error) {
      console.error('Failed to load config:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (values: any) => {
    setSaving(true)
    try {
      await initApi.updateConfig(values)
      message.success('配置已保存')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#f5f5f5',
      padding: 24,
    }}>
      <Card style={{ maxWidth: 800, margin: '0 auto', borderRadius: 12 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
          <Title level={2} style={{ marginTop: 16, marginBottom: 0 }}>
            系统已初始化
          </Title>
          <Text type="secondary">
            您可以配置以下选项，或稍后在设置中修改
          </Text>
        </div>

        <Alert
          message="可选配置"
          description="以下配置均为可选项，您可以跳过或稍后在设置中配置"
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
        >
          {/* API 配置 */}
          <Divider>
            <Space>
              <ApiOutlined />
              <Text>AI 模型配置</Text>
            </Space>
          </Divider>

          <Form.Item
            name="api_base_url"
            label="API Base URL"
            extra="默认使用 OpenRouter"
          >
            <Input placeholder="https://openrouter.ai/api/v1" size="large" />
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API Key"
            extra="您的 OpenRouter API Key 或其他兼容服务的 Key"
          >
            <Input.Password placeholder="sk-xxx..." size="large" />
          </Form.Item>

          <Form.Item
            name="api_model"
            label="默认模型"
          >
            <Input placeholder="z-ai/glm-5" size="large" />
          </Form.Item>

          {/* 代理配置 */}
          <Divider>
            <Space>
              <SettingOutlined />
              <Text>代理配置</Text>
            </Space>
          </Divider>

          <Form.Item name="http_proxy" label="HTTP 代理">
            <Input placeholder="http://127.0.0.1:7890" />
          </Form.Item>

          <Form.Item name="https_proxy" label="HTTPS 代理">
            <Input placeholder="http://127.0.0.1:7890" />
          </Form.Item>

          {/* 存储配置 */}
          <Divider>
            <Space>
              <CloudServerOutlined />
              <Text>存储后端</Text>
            </Space>
          </Divider>

          <Form.Item name="storage_backend" label="存储后端" initialValue="local">
            <Select size="large">
              <Option value="local">本地存储</Option>
              <Option value="s3">AWS S3</Option>
              <Option value="minio">MinIO</Option>
            </Select>
          </Form.Item>

          <Form.Item noStyle shouldUpdate>
            {({ getFieldValue }) => {
              const backend = getFieldValue('storage_backend')
              if (backend === 'local') return null
              return (
                <>
                  <Form.Item name="s3_endpoint" label="Endpoint">
                    <Input placeholder="https://s3.amazonaws.com" />
                  </Form.Item>
                  <Form.Item name="s3_access_key" label="Access Key">
                    <Input placeholder="AKIAIOSFODNN7EXAMPLE" />
                  </Form.Item>
                  <Form.Item name="s3_secret_key" label="Secret Key">
                    <Input.Password placeholder="wJalrXUtnFEMI/K7MDENG" />
                  </Form.Item>
                  <Form.Item name="s3_bucket" label="Bucket">
                    <Input placeholder="my-bucket" />
                  </Form.Item>
                </>
              )
            }}
          </Form.Item>

          <Divider />

          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Button size="large" onClick={() => window.location.href = '/dashboard'}>
              跳过，稍后配置
            </Button>
            <Button type="primary" size="large" htmlType="submit" loading={saving}>
              保存配置
            </Button>
          </Space>
        </Form>
      </Card>
    </div>
  )
}