import { useState, useEffect } from 'react'
import { Form, Input, Button, Card, Steps, Typography, message, Divider, Select, Alert } from 'antd'
import { RocketOutlined, DatabaseOutlined, UserOutlined, ApiOutlined, CloudServerOutlined } from '@ant-design/icons'
import { initApi } from '../api'

const { Title, Text, Paragraph } = Typography
const { Option } = Select

interface InitStatus {
  initialized: boolean
  data_path_configured: boolean
  admin_created: boolean
  api_configured: boolean
  missing_requirements: string[]
}

export default function InitWizard() {
  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(true)
  const [initStatus, setInitStatus] = useState<InitStatus | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    checkInitStatus()
  }, [])

  const checkInitStatus = async () => {
    try {
      const res = await initApi.getStatus()
      setInitStatus(res.data)
      if (res.data.initialized) {
        // Already initialized, redirect to login
        window.location.href = '/login'
      }
    } catch (error) {
      console.error('Failed to check init status:', error)
    } finally {
      setChecking(false)
    }
  }

  const handleFinish = async (values: any) => {
    setLoading(true)
    try {
      await initApi.initialize({
        data_path: values.data_path,
        admin_username: values.admin_username || 'admin',
        admin_email: values.admin_email,
        admin_password: values.admin_password,
        api_base_url: values.api_base_url,
        api_key: values.api_key,
        api_model: values.api_model,
        http_proxy: values.http_proxy,
        https_proxy: values.https_proxy,
        storage_backend: values.storage_backend || 'local',
        s3_endpoint: values.s3_endpoint,
        s3_access_key: values.s3_access_key,
        s3_secret_key: values.s3_secret_key,
        s3_bucket: values.s3_bucket,
      })
      message.success('初始化成功！正在跳转到登录页面...')
      setTimeout(() => {
        window.location.href = '/login'
      }, 1500)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '初始化失败，请检查配置')
    } finally {
      setLoading(false)
    }
  }

  const steps = [
    {
      title: '欢迎',
      icon: <RocketOutlined />,
    },
    {
      title: '数据存储',
      icon: <DatabaseOutlined />,
    },
    {
      title: '管理员账户',
      icon: <UserOutlined />,
    },
    {
      title: 'API配置',
      icon: <ApiOutlined />,
    },
    {
      title: '存储后端',
      icon: <CloudServerOutlined />,
    },
  ]

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <RocketOutlined style={{ fontSize: 64, color: '#1890ff', marginBottom: 24 }} />
            <Title level={2}>欢迎使用 SpatialUnderstandingDataProcess</Title>
            <Paragraph style={{ fontSize: 16, color: '#666' }}>
              空间理解多模态 VLM 训练数据处理平台
            </Paragraph>
            <Paragraph>
              这是首次启动，需要进行一些基础配置。<br />
              整个过程大约需要 2 分钟。
            </Paragraph>
            <Alert
              style={{ marginTop: 24, textAlign: 'left' }}
              message="配置说明"
              description={
                <ul style={{ marginBottom: 0 }}>
                  <li><strong>数据存放地址</strong>（必填）：用于存储数据集、模型、缓存等</li>
                  <li><strong>管理员账户</strong>（必填）：系统第一个用户，拥有管理员权限</li>
                  <li><strong>API配置</strong>（选填）：用于 AI 功能，可稍后在设置中配置</li>
                  <li><strong>存储后端</strong>（选填）：默认本地存储，可选 S3/MinIO</li>
                </ul>
              }
              type="info"
            />
          </div>
        )

      case 1:
        return (
          <div style={{ maxWidth: 600, margin: '0 auto' }}>
            <Title level={4}>配置数据存储路径</Title>
            <Text type="secondary">系统将在此路径下存储数据集、模型、缓存等文件</Text>
            <Divider />
            <Form.Item
              name="data_path"
              label="数据存放地址"
              rules={[{ required: true, message: '请输入数据存放地址' }]}
              extra="例如：/data/spatial 或 D:/spatial-data"
            >
              <Input placeholder="/path/to/your/data" size="large" />
            </Form.Item>
            <Alert
              message="请确保该路径存在且有写入权限"
              type="warning"
              showIcon
            />
          </div>
        )

      case 2:
        return (
          <div style={{ maxWidth: 600, margin: '0 auto' }}>
            <Title level={4}>创建管理员账户</Title>
            <Text type="secondary">这是系统的第一个账户，将自动获得管理员权限</Text>
            <Divider />
            <Form.Item
              name="admin_username"
              label="用户名"
              initialValue="admin"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input prefix={<UserOutlined />} placeholder="admin" size="large" />
            </Form.Item>
            <Form.Item
              name="admin_email"
              label="邮箱"
              rules={[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '请输入有效的邮箱地址' },
              ]}
            >
              <Input placeholder="admin@example.com" size="large" />
            </Form.Item>
            <Form.Item
              name="admin_password"
              label="密码"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 8, message: '密码至少 8 个字符' },
              ]}
            >
              <Input.Password placeholder="至少 8 个字符" size="large" />
            </Form.Item>
            <Form.Item
              name="confirm_password"
              label="确认密码"
              dependencies={['admin_password']}
              rules={[
                { required: true, message: '请确认密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('admin_password') === value) {
                      return Promise.resolve()
                    }
                    return Promise.reject(new Error('两次输入的密码不一致'))
                  },
                }),
              ]}
            >
              <Input.Password placeholder="再次输入密码" size="large" />
            </Form.Item>
          </div>
        )

      case 3:
        return (
          <div style={{ maxWidth: 600, margin: '0 auto' }}>
            <Title level={4}>API 配置（选填）</Title>
            <Text type="secondary">用于 AI 辅助功能，可稍后在设置中配置</Text>
            <Divider />
            <Form.Item
              name="api_base_url"
              label="API Base URL"
              extra="默认使用 OpenRouter，可自定义"
            >
              <Input placeholder="https://openrouter.ai/api/v1" size="large" />
            </Form.Item>
            <Form.Item
              name="api_key"
              label="API Key"
              extra="OpenRouter API Key 或其他兼容服务的 Key"
            >
              <Input.Password placeholder="sk-xxx..." size="large" />
            </Form.Item>
            <Form.Item
              name="api_model"
              label="默认模型"
              initialValue="z-ai/glm-5"
            >
              <Input placeholder="z-ai/glm-5" size="large" />
            </Form.Item>
            <Divider>代理设置（选填）</Divider>
            <Form.Item name="http_proxy" label="HTTP 代理">
              <Input placeholder="http://127.0.0.1:7890" />
            </Form.Item>
            <Form.Item name="https_proxy" label="HTTPS 代理">
              <Input placeholder="http://127.0.0.1:7890" />
            </Form.Item>
          </div>
        )

      case 4:
        return (
          <div style={{ maxWidth: 600, margin: '0 auto' }}>
            <Title level={4}>存储后端（选填）</Title>
            <Text type="secondary">默认使用本地存储，可选 S3 兼容存储</Text>
            <Divider />
            <Form.Item
              name="storage_backend"
              label="存储后端"
              initialValue="local"
            >
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
                      <Input.Password placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" />
                    </Form.Item>
                    <Form.Item name="s3_bucket" label="Bucket Name">
                      <Input placeholder="my-bucket" />
                    </Form.Item>
                  </>
                )
              }}
            </Form.Item>

            <Divider />
            <Alert
              message="准备完成"
              description="点击"完成初始化"按钮开始使用系统"
              type="success"
              showIcon
            />
          </div>
        )

      default:
        return null
    }
  }

  if (checking) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center' 
      }}>
        <Text>正在检查系统状态...</Text>
      </div>
    )
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: 24,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <Card style={{ width: '100%', maxWidth: 800, borderRadius: 12 }}>
        <Steps current={currentStep} items={steps} style={{ marginBottom: 32 }} />
        
        <Form
          form={form}
          layout="vertical"
          onFinish={handleFinish}
        >
          {renderStepContent()}
          
          <Divider />
          
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <Button
              size="large"
              onClick={() => setCurrentStep(currentStep - 1)}
              disabled={currentStep === 0}
            >
              上一步
            </Button>
            
            {currentStep < steps.length - 1 ? (
              <Button
                type="primary"
                size="large"
                onClick={() => {
                  // Validate current step fields
                  const fieldsToValidate: string[] = []
                  switch (currentStep) {
                    case 1:
                      fieldsToValidate.push('data_path')
                      break
                    case 2:
                      fieldsToValidate.push('admin_username', 'admin_email', 'admin_password', 'confirm_password')
                      break
                  }
                  if (fieldsToValidate.length > 0) {
                    form.validateFields(fieldsToValidate)
                      .then(() => setCurrentStep(currentStep + 1))
                      .catch(() => {})
                  } else {
                    setCurrentStep(currentStep + 1)
                  }
                }}
              >
                下一步
              </Button>
            ) : (
              <Button
                type="primary"
                size="large"
                htmlType="submit"
                loading={loading}
              >
                完成初始化
              </Button>
            )}
          </div>
        </Form>
      </Card>
    </div>
  )
}
