import { useState, useEffect } from 'react'
import { Modal, Progress, Spin, Empty, Tag, Space, Typography, Button, message, Alert } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, SyncOutlined } from '@ant-design/icons'
import { tasksApi } from '../api'

const { Text } = Typography

interface DownloadProgressModalProps {
  visible: boolean
  datasetId: number | null
  taskId: number | null
  isNewDataset?: boolean
  onClose: (cancelled: boolean) => void
  onComplete: () => void
}

export default function DownloadProgressModal({
  visible,
  datasetId,
  taskId,
  isNewDataset = false,
  onClose,
  onComplete,
}: DownloadProgressModalProps) {
  const [task, setTask] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (visible && taskId) {
      fetchTask()
      
      // 轮询任务状态（每 2 秒）
      const interval = setInterval(fetchTask, 2000)
      return () => clearInterval(interval)
    }
  }, [visible, taskId])

  const fetchTask = async () => {
    if (!taskId) return
    
    setLoading(true)
    try {
      const { data } = await tasksApi.get(taskId)
      setTask(data)
      
      // 任务完成或失败
      if (data.status === 'completed') {
        message.success('下载完成！')
        onComplete()
      } else if (data.status === 'failed') {
        message.error(`下载失败：${data.error_message || '未知错误'}`)
      }
    } catch (error: any) {
      console.error('获取任务状态失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    if (isNewDataset && task?.status === 'running') {
      message.warning('下载进行中，请勿关闭')
      return
    }
    onClose(false)
  }

  const getProgressStatus = () => {
    if (!task) return 'active'
    
    switch (task.status) {
      case 'completed':
        return 'success'
      case 'failed':
        return 'exception'
      case 'cancelled':
        return 'exception'
      default:
        return 'active'
    }
  }

  const getStatusIcon = () => {
    if (!task) return <SyncOutlined spin />
    
    switch (task.status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'failed':
      case 'cancelled':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default:
        return <SyncOutlined spin style={{ color: '#1890ff' }} />
    }
  }

  const getStatusText = () => {
    if (!task) return '准备中...'
    
    switch (task.status) {
      case 'pending':
        return '等待中...'
      case 'running':
        return task.progress ? `下载中 ${task.progress}%` : '下载中...'
      case 'completed':
        return '下载完成'
      case 'failed':
        return `下载失败：${task.error_message || '未知错误'}`
      case 'cancelled':
        return '已取消'
      default:
        return '未知状态'
    }
  }

  const getProgressPercent = () => {
    if (!task) return 10
    
    if (task.progress) {
      return task.progress
    }
    
    switch (task.status) {
      case 'pending':
        return 10
      case 'running':
        return 50
      case 'completed':
        return 100
      default:
        return 0
    }
  }

  return (
    <Modal
      title={
        <Space>
          {getStatusIcon()}
          <span>下载进度</span>
        </Space>
      }
      open={visible}
      onCancel={handleClose}
      footer={[
        <Button 
          key="close" 
          onClick={handleClose}
          disabled={isNewDataset && task?.status === 'running'}
          type={isNewDataset && task?.status === 'running' ? 'default' : 'primary'}
        >
          {isNewDataset && task?.status === 'running' ? '下载中...' : '关闭'}
        </Button>,
      ]}
      closable={!isNewDataset || task?.status !== 'running'}
      width={500}
    >
      {loading && !task ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin tip="加载任务状态..." />
        </div>
      ) : task ? (
        <div style={{ padding: '20px 0' }}>
          {/* 新建数据集提示 */}
          {isNewDataset && (
            <Alert
              message="新建数据集流程"
              description="下载完成后，数据集将自动出现在列表中"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {/* 状态标签 */}
          <div style={{ marginBottom: 16 }}>
            <Space>
              <Tag color={
                task.status === 'completed' ? 'green' :
                task.status === 'failed' ? 'red' :
                task.status === 'running' ? 'blue' : 'default'
              }>
                {task.status.toUpperCase()}
              </Tag>
              {task.dataset_id && (
                <Text type="secondary">数据集 ID: {task.dataset_id}</Text>
              )}
            </Space>
          </div>

          {/* 进度条 */}
          <Progress
            percent={getProgressPercent()}
            status={getProgressStatus()}
            strokeColor={
              task.status === 'completed' ? '#52c41a' :
              task.status === 'failed' ? '#ff4d4f' : '#1890ff'
            }
            format={(percent) => getStatusText()}
          />

          {/* 详细信息 */}
          {task.error_message && (
            <div style={{ marginTop: 16, padding: 12, background: '#fff1f0', border: '1px solid #ffa4a4', borderRadius: 4 }}>
              <Text type="danger">{task.error_message}</Text>
            </div>
          )}

          {task.started_at && (
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              开始时间：{new Date(task.started_at).toLocaleString()}
            </div>
          )}

          {task.completed_at && (
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              完成时间：{new Date(task.completed_at).toLocaleString()}
            </div>
          )}
        </div>
      ) : (
        <Empty description="无任务信息" />
      )}
    </Modal>
  )
}
