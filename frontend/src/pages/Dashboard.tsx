import { useState, useEffect } from 'react'
import {
  Card, Row, Col, Statistic, Typography, Spin, Progress, Tag, Space, Empty
} from 'antd'
import {
  DatabaseOutlined, FileOutlined, CloudServerOutlined,
  PictureOutlined, VideoCameraOutlined, FileTextOutlined,
  ClockCircleOutlined, ThunderboltOutlined
} from '@ant-design/icons'
import { api } from '../api'

const { Title, Text } = Typography

interface OverviewStats {
  total_datasets: number
  total_files: number
  total_size: number
  files_by_type: Record<string, number>
  files_by_status: Record<string, number>
  new_files_week: number
  pending_tasks: number
  running_tasks: number
}

interface TimelineItem {
  date: string
  count: number
  size: number
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<OverviewStats | null>(null)
  const [timeline, setTimeline] = useState<TimelineItem[]>([])

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [overviewRes, timelineRes] = await Promise.all([
        api.get('/statistics/overview'),
        api.get('/statistics/timeline?days=7'),
      ])
      setStats(overviewRes.data)
      setTimeline(timelineRes.data.timeline || [])
    } catch (error) {
      console.error('Failed to fetch statistics:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
    return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'image': return <PictureOutlined />
      case 'video': return <VideoCameraOutlined />
      case 'text': return <FileTextOutlined />
      default: return <FileOutlined />
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'image': return '#1890ff'
      case 'video': return '#722ed1'
      case 'text': return '#52c41a'
      default: return '#8c8c8c'
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!stats) {
    return <Empty description="暂无数据" />
  }

  return (
    <div>
      <Title level={4}>仪表盘</Title>
      <Text type="secondary">欢迎回来！这是您的数据概览。</Text>

      {/* Main Statistics */}
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="数据集"
              value={stats.total_datasets}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总文件"
              value={stats.total_files}
              prefix={<FileOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="存储空间"
              value={formatSize(stats.total_size)}
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="本周新增"
              value={stats.new_files_week}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
              suffix="个文件"
            />
          </Card>
        </Col>
      </Row>

      {/* Task Status */}
      {(stats.pending_tasks > 0 || stats.running_tasks > 0) && (
        <Card title="任务状态" style={{ marginTop: 24 }}>
          <Space size="large">
            {stats.pending_tasks > 0 && (
              <Statistic
                title="等待中"
                value={stats.pending_tasks}
                prefix={<ClockCircleOutlined />}
              />
            )}
            {stats.running_tasks > 0 && (
              <Statistic
                title="运行中"
                value={stats.running_tasks}
                prefix={<ThunderboltOutlined />}
              />
            )}
          </Space>
        </Card>
      )}

      {/* File Type Distribution */}
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={12}>
          <Card title="文件类型分布">
            {Object.keys(stats.files_by_type).length > 0 ? (
              <Row gutter={[16, 16]}>
                {Object.entries(stats.files_by_type).map(([type, count]) => (
                  <Col span={8} key={type}>
                    <Card size="small" style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, color: getTypeColor(type) }}>
                        {getTypeIcon(type)}
                      </div>
                      <Statistic
                        title={type.toUpperCase()}
                        value={count}
                        valueStyle={{ fontSize: 20 }}
                      />
                    </Card>
                  </Col>
                ))}
              </Row>
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>

        <Col span={12}>
          <Card title="文件状态">
            {Object.keys(stats.files_by_status).length > 0 ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                {Object.entries(stats.files_by_status).map(([status, count]) => {
                  const total = stats.total_files || 1
                  const percent = Math.round((count / total) * 100)
                  return (
                    <div key={status}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <Tag color={status === 'ready' ? 'green' : status === 'error' ? 'red' : 'blue'}>
                          {status}
                        </Tag>
                        <Text type="secondary">{count} ({percent}%)</Text>
                      </div>
                      <Progress percent={percent} showInfo={false} strokeColor={status === 'ready' ? '#52c41a' : status === 'error' ? '#ff4d4f' : '#1890ff'} />
                    </div>
                  )
                })}
              </Space>
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>
      </Row>

      {/* Timeline */}
      {timeline.length > 0 && (
        <Card title="最近7天新增文件" style={{ marginTop: 24 }}>
          <div style={{ display: 'flex', alignItems: 'flex-end', height: 150, gap: 8 }}>
            {timeline.map((item) => {
              const maxCount = Math.max(...timeline.map(t => t.count), 1)
              const height = (item.count / maxCount) * 100
              return (
                <div key={item.date} style={{ flex: 1, textAlign: 'center' }}>
                  <div
                    style={{
                      height: height,
                      minHeight: 4,
                      background: 'linear-gradient(to top, #1890ff, #40a9ff)',
                      borderRadius: '4px 4px 0 0',
                      marginBottom: 8,
                    }}
                  />
                  <div style={{ fontSize: 12, color: '#8c8c8c' }}>
                    {new Date(item.date).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })}
                  </div>
                  <div style={{ fontSize: 12, fontWeight: 'bold' }}>{item.count}</div>
                </div>
              )
            })}
          </div>
        </Card>
      )}

      {/* Quick Actions */}
      <Card title="快速操作" style={{ marginTop: 24 }}>
        <Space size="large">
          <a href="/datasets">📁 管理数据集</a>
          <a href="/api-keys">🔑 管理 API Keys</a>
          <a href="/ai-assistant">🤖 AI 助手</a>
        </Space>
      </Card>
    </div>
  )
}
