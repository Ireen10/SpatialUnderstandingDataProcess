import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card, Typography, Space, Button, Spin, Empty, Row, Col, Tag, Image,
  Tabs, Statistic, Progress, message
} from 'antd'
import {
  ArrowLeftOutlined, EyeOutlined, PlayCircleOutlined, FileTextOutlined,
  PictureOutlined, VideoCameraOutlined, DatabaseOutlined
} from '@ant-design/icons'
import { datasetsApi, api } from '../api'

const { Title, Text } = Typography

interface FileItem {
  id: number
  filename: string
  relative_path: string
  file_size: number
  file_type: string
  data_type: string
  status: string
  paired_text?: string
}

interface PreviewData {
  id: number
  filename: string
  preview_url?: string
  thumbnail_url?: string
  video_url?: string
  content?: string
  paired_text?: string
  metadata?: {
    width?: number
    height?: number
    duration?: number
    fps?: number
  }
}

export default function DatasetVisualizer() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [dataset, setDataset] = useState<any>(null)
  const [files, setFiles] = useState<FileItem[]>([])
  const [previewData, setPreviewData] = useState<Map<number, PreviewData>>(new Map())
  const [activeView, setActiveView] = useState('grid')

  useEffect(() => {
    if (id) {
      fetchData()
    }
  }, [id])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [datasetRes, filesRes] = await Promise.all([
        datasetsApi.get(Number(id)),
        datasetsApi.listFiles(Number(id), { page_size: 100 }),
      ])
      setDataset(datasetRes.data)
      setFiles(filesRes.data.items || [])
      
      // Load previews for first 20 files
      const previewPromises = (filesRes.data.items || []).slice(0, 20).map(async (file: FileItem) => {
        try {
          const { data } = await api.get(`/files/${file.id}/preview`)
          return [file.id, data] as [number, PreviewData]
        } catch {
          return [file.id, null] as [number, null]
        }
      })
      
      const previews = await Promise.all(previewPromises)
      const previewMap = new Map<number, PreviewData>()
      previews.forEach(([fileId, data]) => {
        if (data) previewMap.set(fileId, data)
      })
      setPreviewData(previewMap)
    } catch (error) {
      message.error('加载数据失败')
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

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Calculate statistics
  const stats = {
    total: files.length,
    images: files.filter(f => f.data_type === 'image').length,
    videos: files.filter(f => f.data_type === 'video').length,
    texts: files.filter(f => f.data_type === 'text').length,
    withPairs: files.filter(f => f.paired_text).length,
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!dataset) {
    return <Empty description="数据集不存在" />
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/datasets')}>
          返回
        </Button>
        <Title level={4} style={{ margin: 0 }}>{dataset.name}</Title>
      </Space>

      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card>
            <Statistic title="总文件数" value={stats.total} prefix={<DatabaseOutlined />} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="图像" value={stats.images} prefix={<PictureOutlined />} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="视频" value={stats.videos} prefix={<VideoCameraOutlined />} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="文本" value={stats.texts} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="配对数据" value={stats.withPairs} prefix={<EyeOutlined />} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="总大小" value={formatSize(dataset.total_size)} />
          </Card>
        </Col>
      </Row>

      {/* View Tabs */}
      <Tabs
        activeKey={activeView}
        onChange={setActiveView}
        items={[
          {
            key: 'grid',
            label: '网格视图',
            children: (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16 }}>
                {files.map(file => {
                  const preview = previewData.get(file.id)
                  
                  return (
                    <Card
                      key={file.id}
                      hoverable
                      size="small"
                      cover={
                        file.data_type === 'image' && preview?.thumbnail_url ? (
                          <img src={preview.thumbnail_url} alt={file.filename} style={{ height: 150, objectFit: 'cover' }} />
                        ) : file.data_type === 'video' && preview?.thumbnail_url ? (
                          <div style={{ position: 'relative' }}>
                            <img src={preview.thumbnail_url} alt={file.filename} style={{ width: '100%', height: 150, objectFit: 'cover' }} />
                            <PlayCircleOutlined style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', fontSize: 32, color: 'white' }} />
                          </div>
                        ) : (
                          <div style={{ height: 150, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
                            <FileTextOutlined style={{ fontSize: 48, color: '#999' }} />
                          </div>
                        )
                      }
                    >
                      <Card.Meta
                        title={<Text ellipsis title={file.filename}>{file.filename}</Text>}
                        description={
                          <Space direction="vertical" size={0} style={{ width: '100%' }}>
                            <Text type="secondary" style={{ fontSize: 12 }}>{formatSize(file.file_size)}</Text>
                            {preview?.metadata?.width && (
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                {preview.metadata.width} × {preview.metadata.height}
                              </Text>
                            )}
                            {preview?.metadata?.duration && (
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                {formatDuration(preview.metadata.duration)}
                              </Text>
                            )}
                          </Space>
                        }
                      />
                    </Card>
                  )
                })}
              </div>
            ),
          },
          {
            key: 'pairs',
            label: '配对视图',
            children: (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
                {files.filter(f => f.paired_text).map(file => {
                  const preview = previewData.get(file.id)
                  
                  return (
                    <Card key={file.id} size="small">
                      {file.data_type === 'image' && preview?.preview_url && (
                        <Image src={preview.preview_url} alt={file.filename} style={{ width: '100%', maxHeight: 200, objectFit: 'contain' }} />
                      )}
                      {file.data_type === 'video' && preview?.video_url && (
                        <video src={preview.video_url} controls style={{ width: '100%', maxHeight: 200 }} />
                      )}
                      <Card.Meta
                        title={<Text ellipsis title={file.filename}>{file.filename}</Text>}
                        description={
                          <div style={{ maxHeight: 100, overflow: 'auto', marginTop: 8 }}>
                            <Text style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>
                              {file.paired_text}
                            </Text>
                          </div>
                        }
                      />
                    </Card>
                  )
                })}
              </div>
            ),
          },
          {
            key: 'list',
            label: '列表视图',
            children: (
              <Card>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #f0f0f0' }}>
                      <th style={{ textAlign: 'left', padding: 12 }}>文件名</th>
                      <th style={{ textAlign: 'left', padding: 12 }}>类型</th>
                      <th style={{ textAlign: 'left', padding: 12 }}>大小</th>
                      <th style={{ textAlign: 'left', padding: 12 }}>状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {files.map(file => (
                      <tr key={file.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                        <td style={{ padding: 12 }}>
                          <Text ellipsis style={{ maxWidth: 300 }}>{file.filename}</Text>
                        </td>
                        <td style={{ padding: 12 }}>
                          <Tag color={file.data_type === 'image' ? 'blue' : file.data_type === 'video' ? 'purple' : 'green'}>
                            {file.data_type}
                          </Tag>
                        </td>
                        <td style={{ padding: 12 }}>{formatSize(file.file_size)}</td>
                        <td style={{ padding: 12 }}>
                          <Tag color={file.status === 'ready' ? 'success' : 'warning'}>{file.status}</Tag>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            ),
          },
        ]}
      />
    </div>
  )
}
