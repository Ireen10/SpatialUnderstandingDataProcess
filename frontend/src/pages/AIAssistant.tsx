import { useState } from 'react'
import {
  Card, Typography, Space, Button, Input, Select, message, Divider,
  Tabs, Alert, Spin, Empty, Row, Col, Tag, Modal
} from 'antd'
import {
  CodeOutlined, RobotOutlined, ThunderboltOutlined, FileTextOutlined,
  CopyOutlined, PlayCircleOutlined
} from '@ant-design/icons'
import { api } from '../api'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

export default function AIAssistant() {
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('visualization')
  
  // Visualization state
  const [vizDataType, setVizDataType] = useState('image_text')
  const [vizSampleData, setVizSampleData] = useState('')
  const [vizDescription, setVizDescription] = useState('')
  const [vizCode, setVizCode] = useState('')
  
  // Conversion state
  const [convSource, setConvSource] = useState('')
  const [convTarget, setConvTarget] = useState('')
  const [convSample, setConvSample] = useState('')
  const [convDescription, setConvDescription] = useState('')
  const [convScript, setConvScript] = useState('')
  
  // Chat state
  const [chatMessage, setChatMessage] = useState('')
  const [chatContext, setChatContext] = useState('')
  const [chatResponse, setChatResponse] = useState('')

  const generateVisualization = async () => {
    if (!vizSampleData.trim()) {
      message.warning('请输入示例数据结构')
      return
    }
    
    setLoading(true)
    try {
      const sampleData = JSON.parse(vizSampleData)
      const { data } = await api.post('/ai/generate-visualization', {
        data_type: vizDataType,
        sample_data: sampleData,
        description: vizDescription || undefined,
      })
      setVizCode(data.code)
      message.success('可视化代码生成成功')
    } catch (error: any) {
      if (error instanceof SyntaxError) {
        message.error('示例数据 JSON 格式错误')
      } else {
        message.error(error.response?.data?.detail || '生成失败')
      }
    } finally {
      setLoading(false)
    }
  }

  const generateConversion = async () => {
    if (!convSource.trim() || !convTarget.trim()) {
      message.warning('请输入源格式和目标格式')
      return
    }
    
    setLoading(true)
    try {
      const payload: any = {
        source_format: convSource,
        target_format: convTarget,
        description: convDescription || undefined,
      }
      
      if (convSample.trim()) {
        payload.sample_data = JSON.parse(convSample)
      }
      
      const { data } = await api.post('/ai/generate-conversion-script', payload)
      setConvScript(data.script)
      message.success('转换脚本生成成功')
    } catch (error: any) {
      if (error instanceof SyntaxError) {
        message.error('示例数据 JSON 格式错误')
      } else {
        message.error(error.response?.data?.detail || '生成失败')
      }
    } finally {
      setLoading(false)
    }
  }

  const sendChat = async () => {
    if (!chatMessage.trim()) {
      message.warning('请输入消息')
      return
    }
    
    setLoading(true)
    try {
      const { data } = await api.post('/ai/chat', {
        message: chatMessage,
        context: chatContext || undefined,
      })
      setChatResponse(data.response)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '请求失败')
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  }

  const vizTabs = [
    {
      key: 'visualization',
      label: (
        <span>
          <CodeOutlined />
          可视化生成
        </span>
      ),
      children: (
        <div>
          <Alert
            message="AI 根据数据类型自动生成 HTML 可视化代码"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <Text strong>数据类型</Text>
              <Select
                value={vizDataType}
                onChange={setVizDataType}
                style={{ width: '100%', marginTop: 8 }}
                options={[
                  { value: 'image_text', label: '图像-文本配对' },
                  { value: 'video_text', label: '视频-文本配对' },
                  { value: 'image', label: '纯图像' },
                  { value: 'video', label: '纯视频' },
                  { value: 'text', label: '纯文本' },
                ]}
              />
            </div>
            
            <div>
              <Text strong>示例数据结构 (JSON)</Text>
              <TextArea
                rows={6}
                value={vizSampleData}
                onChange={(e) => setVizSampleData(e.target.value)}
                placeholder={`{
  "items": [
    {"image": "image1.jpg", "text": "描述1"},
    {"image": "image2.jpg", "text": "描述2"}
  ]
}`}
                style={{ marginTop: 8, fontFamily: 'monospace' }}
              />
            </div>
            
            <div>
              <Text strong>额外描述 (可选)</Text>
              <TextArea
                rows={2}
                value={vizDescription}
                onChange={(e) => setVizDescription(e.target.value)}
                placeholder="例如：需要网格布局，每行显示4个..."
                style={{ marginTop: 8 }}
              />
            </div>
            
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={generateVisualization}
              loading={loading}
            >
              生成可视化代码
            </Button>
            
            {vizCode && (
              <>
                <Divider />
                <div style={{ position: 'relative' }}>
                  <Button
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => copyToClipboard(vizCode)}
                    style={{ position: 'absolute', right: 0, top: 0 }}
                  >
                    复制
                  </Button>
                  <Text strong>生成的代码</Text>
                  <pre style={{
                    background: '#1e1e1e',
                    color: '#d4d4d4',
                    padding: 16,
                    borderRadius: 8,
                    marginTop: 8,
                    maxHeight: 400,
                    overflow: 'auto',
                    fontSize: 13,
                  }}>
                    {vizCode}
                  </pre>
                </div>
              </>
            )}
          </Space>
        </div>
      ),
    },
    {
      key: 'conversion',
      label: (
        <span>
          <FileTextOutlined />
          格式转换
        </span>
      ),
      children: (
        <div>
          <Alert
            message="AI 生成 Python 转换脚本"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>源格式</Text>
                <Input
                  value={convSource}
                  onChange={(e) => setConvSource(e.target.value)}
                  placeholder="例如：COCO 格式 JSON"
                  style={{ marginTop: 8 }}
                />
              </Col>
              <Col span={12}>
                <Text strong>目标格式</Text>
                <Input
                  value={convTarget}
                  onChange={(e) => setConvTarget(e.target.value)}
                  placeholder="例如：YOLO txt 格式"
                  style={{ marginTop: 8 }}
                />
              </Col>
            </Row>
            
            <div>
              <Text strong>示例数据 (可选, JSON)</Text>
              <TextArea
                rows={4}
                value={convSample}
                onChange={(e) => setConvSample(e.target.value)}
                placeholder='{"images": [...], "annotations": [...]}'
                style={{ marginTop: 8, fontFamily: 'monospace' }}
              />
            </div>
            
            <div>
              <Text strong>额外说明 (可选)</Text>
              <TextArea
                rows={2}
                value={convDescription}
                onChange={(e) => setConvDescription(e.target.value)}
                placeholder="特殊处理要求..."
                style={{ marginTop: 8 }}
              />
            </div>
            
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={generateConversion}
              loading={loading}
            >
              生成转换脚本
            </Button>
            
            {convScript && (
              <>
                <Divider />
                <div style={{ position: 'relative' }}>
                  <Button
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => copyToClipboard(convScript)}
                    style={{ position: 'absolute', right: 0, top: 0 }}
                  >
                    复制
                  </Button>
                  <Text strong>生成的 Python 脚本</Text>
                  <pre style={{
                    background: '#1e1e1e',
                    color: '#d4d4d4',
                    padding: 16,
                    borderRadius: 8,
                    marginTop: 8,
                    maxHeight: 400,
                    overflow: 'auto',
                    fontSize: 13,
                  }}>
                    {convScript}
                  </pre>
                </div>
              </>
            )}
          </Space>
        </div>
      ),
    },
    {
      key: 'chat',
      label: (
        <span>
          <RobotOutlined />
          AI 助手
        </span>
      ),
      children: (
        <div>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <Text strong>上下文 (可选)</Text>
              <TextArea
                rows={2}
                value={chatContext}
                onChange={(e) => setChatContext(e.target.value)}
                placeholder="相关背景信息..."
                style={{ marginTop: 8 }}
              />
            </div>
            
            <div>
              <Text strong>问题</Text>
              <TextArea
                rows={3}
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder="询问数据处理、格式转换、可视化相关问题..."
                style={{ marginTop: 8 }}
              />
            </div>
            
            <Button
              type="primary"
              icon={<RobotOutlined />}
              onClick={sendChat}
              loading={loading}
            >
              发送
            </Button>
            
            {chatResponse && (
              <>
                <Divider />
                <Text strong>AI 回复</Text>
                <Card style={{ marginTop: 8, background: '#fafafa' }}>
                  <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{chatResponse}</Paragraph>
                </Card>
              </>
            )}
          </Space>
        </div>
      ),
    },
  ]

  return (
    <div>
      <Title level={4}>
        <RobotOutlined style={{ marginRight: 8 }} />
        AI 助手
      </Title>
      <Paragraph type="secondary">
        使用 GLM-5 生成可视化代码、转换脚本，或咨询数据处理问题
      </Paragraph>
      
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={vizTabs}
      />
    </div>
  )
}
