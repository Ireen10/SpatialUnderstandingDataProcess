import React from 'react';
import { Modal, Form, Input } from 'antd';

interface ExecutionInputDialogProps {
  open: boolean;
  flowInputs: any[];
  values: Record<string, any>;
  onConfirm: (values: Record<string, any>) => void;
  onCancel: () => void;
}

export const ExecutionInputDialog: React.FC<ExecutionInputDialogProps> = ({ open, flowInputs = [], values = {}, onConfirm, onCancel }) => {
  const [form] = Form.useForm();

  return (
    <Modal title="配置流程输入" open={open} onOk={() => form.submit()} onCancel={onCancel} width={500}>
      <Form form={form} initialValues={values} onFinish={onConfirm} layout="vertical">
        {flowInputs.map((input, idx) => (
          <Form.Item
            key={idx}
            name={input.port}
            label={`${input.port} (${input.type})`}
            rules={[{ required: input.required, message: `请输入 ${input.port}` }]}
          >
            <Input placeholder={`请输入 ${input.port}`} />
          </Form.Item>
        ))}
        {flowInputs.length === 0 && <p style={{ color: '#999', textAlign: 'center' }}>该流程不需要输入参数</p>}
      </Form>
    </Modal>
  );
};

export default ExecutionInputDialog;
