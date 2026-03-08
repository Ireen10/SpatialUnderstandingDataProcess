import { Typography } from 'antd'

const { Title, Paragraph } = Typography

export default function Dashboard() {
  return (
    <div>
      <Title level={4}>仪表盘</Title>
      <Paragraph>欢迎使用空间理解多模态 VLM 训练数据处理平台</Paragraph>
    </div>
  )
}
