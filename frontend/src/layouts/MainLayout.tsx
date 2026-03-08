import { Outlet } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  DatabaseOutlined,
  KeyOutlined,
  SettingOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/auth'

const { Sider, Content, Header } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/datasets', icon: <DatabaseOutlined />, label: '数据集' },
  { key: '/api-keys', icon: <KeyOutlined />, label: 'API Keys' },
  { key: '/settings', icon: <SettingOutlined />, label: '设置' },
]

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={200} theme="light">
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid #f0f0f0' }}>
          <strong>SUDP</strong>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 16 }}>{user?.username || '用户'}</span>
          <a onClick={handleLogout} style={{ color: '#666' }}>
            <LogoutOutlined /> 退出
          </a>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
