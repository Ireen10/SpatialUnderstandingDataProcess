import { useState, useEffect } from 'react'
import { Form, Input, Button, Card, Typography, message, Alert, Modal } from 'antd'
import { UserOutlined, MailOutlined, LockOutlined, RocketOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authApi, initApi } from '../api'

const { Title, Text } = Typography

export default function FirstTimeSetup() {
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const [form] = Form.useForm()

  // 检查是否已初始化
  useEffect(() => {
    initApi.getStatus()
      .then(res => {
        if (res.data.initialized) {
          navigate('/login')
        }
        setChecking(false)
      })
      .catch((err) => {
        setChecking(false)
        const detail = err.response?.data?.detail || err.message
        setError(`无法连接后端服务: ${detail}`)
      })
  }, [])

  const handleFinish = async (values: any) => {
    setLoading(true)
    setError(null)
    
    try {
      // 1. 初始化系统
      const initData = {
        data_path: values.data_path || '../data',
        admin_username: values.username || 'admin',
        admin_email: values.email,
        admin_password: values.password,
      }
      
      await initApi.initialize(initData)

      // 保存 token 并获取用户信息
      const loginRes = await authApi.login(values.username || 'admin', values.password)
      const token = loginRes.data.access_token

      // 保存 token 到 localStorage
      localStorage.setItem('auth-storage', JSON.stringify({
        state: { token, user: { username: values.username || 'admin' } },
        version: 0
      }))

      message.success('注册成功！正在跳转...')
      
      // 直接跳转到 dashboard（使用 replace 避免回退到注册页）
      window.location.href = '/dashboard'
      
    } catch (err: any) {
      console.error('Registration error:', err)
      
      let errorMsg = '注册失败，请稍后重试'
      
      if (err.response) {
        const status = err.response.status
        const detail = err.response.data?.detail
        
        if (status === 404) {
          errorMsg = '服务未就绪，请确保后端服务已启动并更新到最新版本'
        } else if (status === 400) {
          errorMsg = detail || '请求参数有误'
        } else if (status === 500) {
          errorMsg = '服务器内部错误，请查看后端日志'
        } else {
          errorMsg = detail || `请求失败 (${status})`
        }
      } else if (err.request) {
        errorMsg = '无法连接到服务器，请检查网络连接'
      } else {
        errorMsg = err.message || '未知错误'
      }
      
      setError(errorMsg)
      Modal.error({
        title: '注册失败',
        content: errorMsg,
      })
    } finally {
      setLoading(false)
    }
  }

  if (checking) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
        <Text>检查系统状态...</Text>
        {error && (
          <Alert
            type="error"
            message={error}
            style={{ maxWidth: 400 }}
          />
        )}
      </div>
    )
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 24,
    }}>
      <Card style={{ width: '100%', maxWidth: 480, borderRadius: 12 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <RocketOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          <Title level={2} style={{ marginTop: 16, marginBottom: 0 }}>
            Welcome
          </Title>
          <Text type="secondary">
            SpatialUnderstandingDataProcess
          </Text>
        </div>

        <Alert
          message="First Time Setup"
          description="Please create an admin account to get started"
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        {error && (
          <Alert
            type="error"
            message={error}
            showIcon
            style={{ marginBottom: 24 }}
            closable
            onClose={() => setError(null)}
          />
        )}

        <Form
          form={form}
          layout="vertical"
          onFinish={handleFinish}
          initialValues={{ data_path: '../data' }}
        >
          <Form.Item
            name="username"
            label="Username"
            rules={[{ required: true, message: 'Please enter username' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="admin" size="large" />
          </Form.Item>

          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Please enter email' },
              { type: 'email', message: 'Invalid email format' },
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="admin@example.com" size="large" />
          </Form.Item>

          <Form.Item
            name="password"
            label="Password"
            rules={[
              { required: true, message: 'Please enter password' },
              { min: 8, message: 'Password must be at least 8 characters' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="At least 8 characters" size="large" />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="Confirm Password"
            dependencies={['password']}
            rules={[
              { required: true, message: 'Please confirm password' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('Passwords do not match'))
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Re-enter password" size="large" />
          </Form.Item>

          <Form.Item
            name="data_path"
            label="Data Storage Path"
            extra="Default: ./data folder"
          >
            <Input placeholder="./data" size="large" />
          </Form.Item>

          <Button
            type="primary"
            htmlType="submit"
            size="large"
            block
            loading={loading}
          >
            Complete Registration
          </Button>
        </Form>
      </Card>
    </div>
  )
}