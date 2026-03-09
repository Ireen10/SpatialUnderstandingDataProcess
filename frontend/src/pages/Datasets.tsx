import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Table, Button, Modal, Form, Input, message, Popconfirm, Space, Typography,
  Card, Tag, Select, Tooltip
} from 'antd'
import {
  PlusOutlined, DeleteOutlined, DownloadOutlined,
  ScanOutlined, EyeOutlined, TableOutlined, FolderOutlined
} from '@ant-design/icons'
import { datasetsApi, tasksApi } from '../api'
import DownloadProgressModal from '../components/DownloadProgressModal'
import type { ColumnsType } from 'antd/es/table'

const { Title } = Typography

interface DatasetItem {
  id: number
  name: string
  description?: string
  storage_path: string
  total_files: number
  total_size: number
  version: string
  created_at: string
}

interface FileItem {
  id: number
  filename: string
  relative_path: string
  file_size: number
  file_type: string
  data_type: string
  status: string
  created_at: string
}

export default function Datasets() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [datasets, setDatasets] = useState<DatasetItem[]>([])
  const [files, setFiles] = useState<FileItem[]>([])
  const [selectedDataset, setSelectedDataset] = useState<DatasetItem | null>(null)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [downloadModalVisible, setDownloadModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [downloadForm] = Form.useForm()
  const [downloadLoading, setDownloadLoading] = useState(false)
  const [progressVisible, setProgressVisible] = useState(false)
  const [currentTaskId, setCurrentTaskId] = useState<number | null>(null)

  const fetchDatasets = async () => {
    setLoading(true)
    try {
      const { data } = await datasetsApi.list()
      setDatasets(data.items || [])
    } catch (error) {
      message.error('获取数据集失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchFiles = async (datasetId: number) => {
    try {
      const { data } = await datasetsApi.listFiles(datasetId)
      setFiles(data.items || [])
    } catch (error) {
      message.error('获取文件列表失败')
    }
  }

  useEffect(() => {
    fetchDatasets()
  }, [])

  useEffect(() => {
    if (selectedDataset) {
      fetchFiles(selectedDataset.id)
    }
  }, [selectedDataset])

  const handleCreate = async (values: { name: string; description?: string; storage_path?: string }) => {
    try {
      await datasetsApi.create({
        name: values.name,
        description: values.description,
        storage_path: values.storage_path || 'datasets',
      })
      message.success('创建成功')
      setCreateModalVisible(false)
      form.resetFields()
      fetchDatasets()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await datasetsApi.delete(id)
      message.success('删除成功')
      if (selectedDataset?.id === id) {
        setSelectedDataset(null)
      }
      fetchDatasets()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleScan = async (id: number) => {
    try {
      const { data } = await datasetsApi.scan(id)
      message.success(data.message)
      fetchDatasets()
      if (selectedDataset?.id === id) {
        fetchFiles(id)
      }
    } catch (error) {
      message.error('扫描失败')
    }
  }

  const handleDownload = async (values: { type: 'huggingface' | 'url'; repo_id?: string; url?: string; allow_patterns?: string }) => {
    if (!selectedDataset) return
    
    setDownloadLoading(true)
    try {
      let taskId: number | null = null
      
      if (values.type === 'huggingface') {
        const { data } = await datasetsApi.downloadFromHuggingface(selectedDataset.id, values.repo_id!, values.allow_patterns)
        taskId = data.task_id || null
      } else {
        const { data } = await datasetsApi.downloadFromUrl(selectedDataset.id, values.url!)
        taskId = data.task_id || null
      }
      
      message.success('下载任务已创建')
      setDownloadModalVisible(false)
      downloadForm.resetFields()
      
      // 显示进度弹窗
      if (taskId) {
        setCurrentTaskId(taskId)
        setProgressVisible(true)
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建下载任务失败')
    } finally {
      setDownloadLoading(false)
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
    return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
  }

  const datasetColumns: ColumnsType<DatasetItem> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <a onClick={() => setSelectedDataset(record)}>{text}</a>
      ),
    },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '文件数', dataIndex: 'total_files', key: 'total_files', width: 80 },
    {
      title: '大小',
      dataIndex: 'total_size',
      key: 'total_size',
      width: 100,
      render: (size) => formatSize(size),
    },
    { title: '版本', dataIndex: 'version', key: 'version', width: 80 },
    {
      title: '操作',
      key: 'actions',
      width: 250,
      render: (_, record) => (
        <Space>
          <Tooltip title="扫描文件">
            <Button size="small" icon={<ScanOutlined />} onClick={() => handleScan(record.id)} />
          </Tooltip>
          <Tooltip title="下载">
            <Button size="small" icon={<DownloadOutlined />} onClick={() => { setSelectedDataset(record); setDownloadModalVisible(true) }} />
          </Tooltip>
          <Tooltip title="文件树">
            <Button size="small" icon={<FolderOutlined />} onClick={() => navigate(`/datasets/${record.id}/files`)} />
          </Tooltip>
          <Tooltip title="通用浏览">
            <Button size="small" icon={<TableOutlined />} onClick={() => navigate(`/datasets/${record.id}/view`)} />
          </Tooltip>
          <Tooltip title="可视化">
            <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/datasets/${record.id}/visualize`)} />
          </Tooltip>
          <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const fileColumns: ColumnsType<FileItem> = [
    { title: '文件名', dataIndex: 'filename', key: 'filename', ellipsis: true },
    {
      title: '类型',
      dataIndex: 'data_type',
      key: 'data_type',
      width: 80,
      render: (type) => {
        const colors: Record<string, string> = { image: 'blue', video: 'purple', text: 'green' }
        return <Tag color={colors[type] || 'default'}>{type}</Tag>
      },
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size) => formatSize(size),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status) => {
        const colors: Record<string, string> = { ready: 'success', pending: 'processing', error: 'error' }
        return <Tag color={colors[status] || 'default'}>{status}</Tag>
      },
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4}>
          {selectedDataset ? (
            <Space>
              <a onClick={() => setSelectedDataset(null)}>数据集</a>
              <span>/</span>
              <span>{selectedDataset.name}</span>
            </Space>
          ) : '数据集管理'}
        </Title>
        {!selectedDataset && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
            新建数据集
          </Button>
        )}
        {selectedDataset && (
          <Space>
            <Button icon={<ScanOutlined />} onClick={() => handleScan(selectedDataset.id)}>
              扫描文件
            </Button>
            <Button icon={<DownloadOutlined />} onClick={() => setDownloadModalVisible(true)}>
              下载数据
            </Button>
          </Space>
        )}
      </div>

      {!selectedDataset ? (
        <Table
          columns={datasetColumns}
          dataSource={datasets}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      ) : (
        <Card>
          <Table
            columns={fileColumns}
            dataSource={files}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 20 }}
            locale={{ emptyText: '暂无文件，点击"扫描文件"或"下载数据"添加' }}
          />
        </Card>
      )}

      {/* 创建数据集模态框 */}
      <Modal
        title="新建数据集"
        open={createModalVisible}
        onCancel={() => { setCreateModalVisible(false); form.resetFields() }}
        onOk={() => form.submit()}
        okText="创建"
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="数据集名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="可选描述" />
          </Form.Item>
          <Form.Item name="storage_path" label="存储路径" initialValue="datasets">
            <Input placeholder="相对路径，如 datasets/my-dataset" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 下载数据模态框 */}
      <Modal
        title="下载数据"
        open={downloadModalVisible}
        onCancel={() => { setDownloadModalVisible(false); downloadForm.resetFields() }}
        onOk={() => downloadForm.submit()}
        okText="开始下载"
        confirmLoading={downloadLoading}
      >
        <Form form={downloadForm} layout="vertical" onFinish={handleDownload}>
          <Form.Item name="type" label="下载源" initialValue="huggingface" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="huggingface">HuggingFace Hub</Select.Option>
              <Select.Option value="url">自定义 URL</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prev, curr) => prev.type !== curr.type}
          >
            {({ getFieldValue }) => {
              const type = getFieldValue('type')
              if (type === 'huggingface') {
                return (
                  <>
                    <Form.Item name="repo_id" label="Repo ID" rules={[{ required: true, message: '请输入 HuggingFace Repo ID' }]}>
                      <Input placeholder="例如: username/dataset-name" />
                    </Form.Item>
                    <Form.Item name="allow_patterns" label="包含模式（可选）">
                      <Input placeholder="例如: *.jpg,*.json （逗号分隔）" />
                    </Form.Item>
                  </>
                )
              }
              return (
                <Form.Item name="url" label="下载 URL" rules={[{ required: true, message: '请输入下载链接' }]}>
                  <Input placeholder="https://example.com/dataset.zip" />
                </Form.Item>
              )
            }}
          </Form.Item>
        </Form>
      </Modal>

      {/* 下载进度弹窗 */}
      <DownloadProgressModal
        visible={progressVisible}
        datasetId={selectedDataset?.id || null}
        taskId={currentTaskId}
        onClose={() => {
          setProgressVisible(false)
          setCurrentTaskId(null)
          fetchDatasets() // 刷新列表
          if (selectedDataset) {
            fetchFiles(selectedDataset.id)
          }
        }}
        onComplete={() => {
          // 下载完成后自动刷新
          fetchDatasets()
          if (selectedDataset) {
            fetchFiles(selectedDataset.id)
          }
        }}
      />
    </div>
  )
}
