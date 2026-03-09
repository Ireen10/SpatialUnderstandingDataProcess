import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  Card, Typography, Spin, Empty, Row, Col, Pagination, Image, Tag, Space, Button, message, Divider
} from 'antd'
import {
  PictureOutlined, VideoCameraOutlined, FileTextOutlined, DownloadOutlined
} from '@ant-design/icons'
import api from '../api'

const { Title, Text, Paragraph } = Typography

interface ImageInfo {
  type: 'local' | 'path' | 'unsupported'
  path: string
  message?: string
}

interface RecordData {
  [key: string]: any
  _images?: ImageInfo[]
  _video_cover?: ImageInfo | null
}

interface PreviewResponse {
  dataset_id: number
  dataset_name: string
  total: number
  page: number
  page_size: number
  total_pages: number
  data: RecordData[]
  image_field?: string | null
  has_video: boolean
  fields: string[]
}

export default function UniversalViewer() {
  const { id } = useParams<{ id: string }>()
  const [loading, setLoading] = useState(true)
  const [previewData, setPreviewData] = useState<PreviewResponse | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 50

  useEffect(() => {
    if (id) {
      fetchPreview(currentPage)
    }
  }, [id, currentPage])

  const fetchPreview = async (page: number) => {
    setLoading(true)
    try {
      const { data } = await api.get(`/preview/datasets/${id}?page=${page}`)
      setPreviewData(data)
    } catch (error: any) {
      console.error('加载预览失败:', error)
      message.error(error.response?.data?.detail || '加载预览失败')
    } finally {
      setLoading(false)
    }
  }

  const getOtherFields = (record: RecordData, imageField?: string | null) => {
    const excludedFields = ['_images', '_video_cover']
    if (imageField) excludedFields.push(imageField)
    
    const otherFields: Record<string, any> = {}
    Object.keys(record).forEach(key => {
      if (!excludedFields.includes(key)) {
        otherFields[key] = record[key]
      }
    })
    return otherFields
  }

  const renderMedia = (record: RecordData, imageField?: string | null) => {
    const images = record._images || []
    const videoCover = record._video_cover

    // 有视频封面（优先显示）
    if (videoCover && videoCover.type === 'local') {
      return (
        <div style={{ position: 'relative' }}>
          <Image
            src={`file://${videoCover.path}`}
            alt="视频封面"
            style={{ width: '100%', height: 200, objectFit: 'cover' }}
            preview={{
              src: `file://${videoCover.path}`,
            }}
            fallback="/placeholder-video.png"
          />
          <div
            style={{
              position: 'absolute',
              top: 8,
              right: 8,
              background: 'rgba(0,0,0,0.7)',
              color: '#fff',
              padding: '4px 8px',
              borderRadius: 4,
              fontSize: 12,
            }}
          >
            <VideoCameraOutlined /> 视频
          </div>
        </div>
      )
    }

    // 有多张图片
    if (images.length > 0) {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {images.map((img, idx) => (
            <Image
              key={idx}
              src={img.type === 'local' ? `file://${img.path}` : img.path}
              alt={`图片 ${idx + 1}`}
              style={{ width: '100%', maxHeight: 300, objectFit: 'contain' }}
              fallback="/placeholder-image.png"
            />
          ))}
        </div>
      )
    }

    // 没有媒体
    return (
      <div
        style={{
          width: '100%',
          height: 200,
          background: '#f5f5f5',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#999',
        }}
      >
        <FileTextOutlined style={{ fontSize: 48 }} />
      </div>
    )
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" tip="加载数据中..." />
      </div>
    )
  }

  if (!previewData || previewData.data.length === 0) {
    return (
      <Empty description="暂无数据" style={{ padding: 100 }} />
    )
  }

  return (
    <div style={{ padding: 24 }}>
      {/* 头部信息 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>{previewData.dataset_name}</Title>
        <Space wrap>
          <Tag color="blue">共 {previewData.total} 条</Tag>
          <Tag color="green">
            第 {previewData.page} / {previewData.total_pages} 页
          </Tag>
          {previewData.image_field && (
            <Tag icon={<PictureOutlined />} color="cyan">
              图片字段：{previewData.image_field}
            </Tag>
          )}
          {previewData.has_video && (
            <Tag icon={<VideoCameraOutlined />} color="orange">
              包含视频
            </Tag>
          )}
        </Space>
      </div>

      {/* 卡片网格 */}
      <Row gutter={[16, 16]}>
        {previewData.data.map((record, index) => {
          const otherFields = getOtherFields(record, previewData.image_field)
          const globalIndex = (previewData.page - 1) * previewData.page_size + index + 1

          return (
            <Col xs={24} sm={12} md={8} lg={6} xl={4} key={index}>
              <Card
                hoverable
                size="small"
                cover={renderMedia(record, previewData.image_field)}
                style={{ height: '100%' }}
              >
                <div style={{ fontSize: 12, color: '#999', marginBottom: 8 }}>
                  #{globalIndex}
                </div>
                
                {/* 其他字段 JSON 展示 */}
                {Object.keys(otherFields).length > 0 && (
                  <Paragraph
                    copyable
                    ellipsis={{ rows: 3, expandable: true }}
                    style={{
                      fontSize: 11,
                      background: '#f9f9f9',
                      padding: 8,
                      borderRadius: 4,
                      maxHeight: 100,
                      overflow: 'auto',
                    }}
                  >
                    <pre style={{ margin: 0, fontSize: 'inherit' }}>
                      {JSON.stringify(otherFields, null, 2)}
                    </pre>
                  </Paragraph>
                )}
              </Card>
            </Col>
          )
        })}
      </Row>

      {/* 分页 */}
      <Divider />
      <div style={{ textAlign: 'center', marginTop: 24 }}>
        <Pagination
          current={previewData.page}
          total={previewData.total}
          pageSize={previewData.page_size}
          showTotal={(total) => `共 ${total} 条`}
          showSizeChanger={false}
          onChange={(page) => setCurrentPage(page)}
          disabled={loading}
        />
      </div>
    </div>
  )
}
