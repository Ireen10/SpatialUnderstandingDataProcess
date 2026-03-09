import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Tree, Typography, Space, Tag, Button, Modal, message, Spin, Empty, Card, Statistic, Row, Col
} from 'antd'
import {
  FileTextOutlined, PictureOutlined, VideoCameraOutlined, FileOutlined,
  ArrowLeftOutlined, EyeOutlined, DownloadOutlined, FolderOutlined
} from '@ant-design/icons'
import api, { datasetsApi } from '../api'

const { Title, Text } = Typography
const { DirectoryTree } = Tree

interface TreeNode {
  name: string
  is_dir: boolean
  path: string
  children?: TreeNode[]
  file_count: number
  total_size: number
}

interface TreeResponse {
  dataset_id: number
  dataset_name: string
  total_files: number
  total_size: number
  tree: TreeNode
}

export default function DatasetFiles() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [treeData, setTreeData] = useState<TreeResponse | null>(null)
  const [previewVisible, setPreviewVisible] = useState(false)
  const [previewContent, setPreviewContent] = useState('')
  const [previewFilename, setPreviewFilename] = useState('')
  const [previewLoading, setPreviewLoading] = useState(false)

  useEffect(() => {
    if (id) {
      fetchTree()
    }
  }, [id])

  const fetchTree = async () => {
    setLoading(true)
    try {
      const { data } = await api.get(`/datasets/${id}/tree`)
      setTreeData(data)
    } catch (error: any) {
      console.error('加载文件树失败:', error)
      message.error(error.response?.data?.detail || '加载文件树失败')
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

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(ext || '')) {
      return <PictureOutlined style={{ color: '#1890ff' }} />
    }
    if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(ext || '')) {
      return <VideoCameraOutlined style={{ color: '#722ed1' }} />
    }
    if (['txt', 'md', 'json', 'jsonl', 'csv', 'tsv'].includes(ext || '')) {
      return <FileTextOutlined style={{ color: '#52c41a' }} />
    }
    return <FileOutlined style={{ color: '#8c8c8c' }} />
  }

  const handleFileClick = async (node: any) => {
    if (node.is_dir) return
    
    const ext = node.name.split('.').pop()?.toLowerCase()
    const textExts = ['txt', 'md', 'json', 'jsonl', 'csv', 'tsv', 'xml', 'html']
    
    if (textExts.includes(ext || '')) {
      await previewFile(node.fileId || node.id)
    } else {
      message.info('该文件格式暂不支持预览')
    }
  }

  const previewFile = async (fileId: number) => {
    setPreviewLoading(true)
    try {
      const { data } = await api.get(`/files/${fileId}/preview?max_lines=500`)
      setPreviewContent(data.content)
      setPreviewFilename(data.filename)
      setPreviewVisible(true)
    } catch (error: any) {
      console.error('预览失败:', error)
      message.error(error.response?.data?.detail || '预览失败')
    } finally {
      setPreviewLoading(false)
    }
  }

  const renderTreeIcon = (node: TreeNode) => {
    if (node.is_dir) {
      return <FolderOutlined style={{ color: '#faad14' }} />
    }
    return getFileIcon(node.name)
  }

  const createTreeData = (node: TreeNode, parentId: string = ''): any[] => {
    const key = `${parentId}/${node.name}`
    
    // 查找对应的 fileId（从 API 响应中匹配 path）
    const findFileId = (path: string): number | null => {
      // 这里需要通过 path 查找 fileId，暂时简化处理
      return null
    }
    
    return [{
      title: (
        <Space>
          {renderTreeIcon(node)}
          <span>{node.name}</span>
          {node.is_dir && (
            <Tag color="blue" style={{ fontSize: 10 }}>
              {node.file_count} 文件
            </Tag>
          )}
          {!node.is_dir && (
            <Text type="secondary" style={{ fontSize: 10 }}>
              {formatSize(node.total_size)}
            </Text>
          )}
        </Space>
      ),
      key,
      isLeaf: !node.is_dir,
      children: node.children?.map(child => createTreeData(child, key)),
      is_dir: node.is_dir,
      path: node.path,
      fileId: findFileId(node.path),
    }]
  }

  // 重新加载文件树并附加 fileId
  const loadTreeWithFiles = async () => {
    try {
      const [treeRes, filesRes] = await Promise.all([
        api.get(`/datasets/${id}/tree`),
        datasetsApi.listFiles(Number(id), { page_size: 1000 }),
      ])
      
      const treeData = treeRes.data
      const files = filesRes.data.items || []
      
      // 创建 path 到 fileId 的映射
      const pathToFileId: Record<string, number> = {}
      files.forEach((f: any) => {
        pathToFileId[f.relative_path] = f.id
      })
      
      // 递归附加 fileId
      const attachFileId = (node: TreeNode): any => {
        const fileId = pathToFileId[node.path]
        return {
          title: (
            <Space>
              {renderTreeIcon(node)}
              <span>{node.name}</span>
              {node.is_dir ? (
                <Tag color="blue" style={{ fontSize: 10 }}>
                  {node.file_count} 文件
                </Tag>
              ) : (
                <Text type="secondary" style={{ fontSize: 10 }}>
                  {formatSize(node.total_size)}
                </Text>
              )}
            </Space>
          ),
          key: node.path,
          isLeaf: !node.is_dir,
          children: node.children?.map(attachFileId),
          is_dir: node.is_dir,
          path: node.path,
          fileId: fileId,
        }
      }
      
      setTreeData({ ...treeData, tree: attachFileId(treeData.tree) })
    } catch (error: any) {
      console.error('加载失败:', error)
      message.error('加载文件树失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) {
      loadTreeWithFiles()
    }
  }, [id])

  const treeDataList = treeData ? [createTreeData(treeData.tree)] : []

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" tip="加载文件树..." />
      </div>
    )
  }

  if (!treeData) {
    return <Empty description="暂无数据" style={{ padding: 100 }} />
  }

  return (
    <div style={{ padding: 24 }}>
      {/* 头部 */}
      <div style={{ marginBottom: 24 }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/datasets')}>
            返回
          </Button>
          <Title level={4} style={{ margin: 0 }}>
            {treeData.dataset_name}
          </Title>
        </Space>
        
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={8}>
            <Card size="small">
              <Statistic 
                title="总文件数" 
                value={treeData.total_files} 
                suffix="个"
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card size="small">
              <Statistic 
                title="总大小" 
                value={formatSize(treeData.total_size)}
              />
            </Card>
          </Col>
        </Row>
      </div>

      {/* 文件树 */}
      <Card title="文件结构">
        <DirectoryTree
          treeData={[treeData.tree]}
          onSelect={(_, info) => {
            if (!info.node.is_dir && info.node.fileId) {
              handleFileClick(info.node)
            }
          }}
          defaultExpandAll={true}
          showIcon={true}
        />
      </Card>

      {/* 预览弹窗 */}
      <Modal
        title={
          <Space>
            <FileTextOutlined />
            <span>{previewFilename}</span>
          </Space>
        }
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            关闭
          </Button>,
          <Button 
            key="download" 
            type="primary" 
            icon={<DownloadOutlined />}
            onClick={() => {
              // TODO: 实现下载
              message.info('下载功能开发中')
            }}
          >
            下载
          </Button>,
        ]}
      >
        {previewLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin tip="加载预览..." />
          </div>
        ) : (
          <pre
            style={{
              maxHeight: 500,
              overflow: 'auto',
              background: '#f5f5f5',
              padding: 16,
              borderRadius: 4,
              fontSize: 12,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
            }}
          >
            {previewContent}
          </pre>
        )}
      </Modal>
    </div>
  )
}
