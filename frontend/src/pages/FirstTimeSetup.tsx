import { useState } from 'react'
import { Form, Input, Button, Card, Typography, message, Alert } from 'antd'
import { UserOutlined, MailOutlined, LockOutlined, RocketOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authApi, initApi } from '../api'

const { Title, Text } = Typography

export default function FirstTimeSetup() {
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(true)
  const navigate = useNavigate()
  const [form] = Form.useForm()

  // 检查是否已初始化
  useState(() => {
    initApi.getStatus().then(res => {
      if (res.data.initialized) {
        // 已初始化，跳转到登录
        navigate('/login')
      }
      setChecking(false)
    }).catch(() => {
      setChecking(false)
    })
  }, [])

  const handleFinish = async (values: any) => {
    setLoading(true)
    try {
      // 1. 初始化系统（设置数据路径）
      await initApi.initialize({
        data_path: values.data_path || './data',
        admin_username: values.username,
        admin_email: values.email,
        admin_password: values.password,
      })

      // 2. 自动登录
      const loginRes = await authApi.login(values.username, values.password)
      const token = loginRes.data.access_token

      // 保存 token
      localStorage.setItem('auth-storage', JSON.stringify({
        state: { token, user: { username: values.username } },
        version: 0
      }))

      message.success('注册成功！请配置系统。')
      navigate('/setup/config')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '注册失败')
    } finally {
      setLoading(false)
    }
  }

  if (checking) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Text>检查系统状态...</Text>
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
            欢迎使用
          </Title>
          <Text type="secondary">
            SpatialUnderstandingDataProcess
          </Text>
        </div>

        <Alert
          message="首次使用"
          description="请创建管理员账户完成初始化"
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Form
          form={form}
          layout="vertical"
          onFinish={handleFinish}
          initialValues={{ data_path: './data' }}
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="admin" size="large" />
          </Form.Item>

          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '邮箱格式不正确' },
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="admin@example.com" size="large" />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 8, message: '密码至少 8 个字符' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="至少 8 个字符" size="large" />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="确认密码"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="再次输入密码" size="large" />
          </Form.Item>

          <Form.Item
            name="data_path"
            label="数据存储路径"
            extra="默认为当前目录下的 data 文件夹"
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
            完成注册
          </Button>
        </Form>
      </Card>
    </div>
  )
}