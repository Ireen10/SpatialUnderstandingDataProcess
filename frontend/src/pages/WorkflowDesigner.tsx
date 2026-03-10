import React, { useState, useCallback, useRef } from 'react';
import ReactFlow, { Node, Edge, Controls, Background, useNodesState, useEdgesState, Connection, MarkerType, Panel, ReactFlowInstance } from 'reactflow';
import 'reactflow/dist/style.css';
import { Button, Space, message, Modal } from 'antd';
import { PlayCircleOutlined, SaveOutlined, ClearOutlined } from '@ant-design/icons';
import { ModuleNode } from '../components/workflow/ModuleNode';
import { ExecutionInputDialog } from '../components/workflow/ExecutionInputDialog';
import { executeFlow, createFlow, FlowDefinition } from '../api/flowExecute';

const nodeTypes = { module: ModuleNode };
const moduleTemplates = [
  { category: '输入', type: 'input_adapter', items: [{ label: '数字输入', moduleName: 'number_input', inputs: [], outputs: [{ port: 'numbers', type: 'list' }] }] },
  { category: '处理', type: 'processor', items: [{ label: '求和', moduleName: 'sum_numbers', inputs: [{ port: 'numbers', type: 'list' }], outputs: [{ port: 'sum', type: 'float' }] }] },
];

export const WorkflowDesigner: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [executing, setExecuting] = useState(false);
  const [showInputModal, setShowInputModal] = useState(false);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);

  const onDragStart = (event: React.DragEvent, nodeData: any) => { event.dataTransfer.effectAllowed = 'move'; event.dataTransfer.setData('application/reactflow', JSON.stringify(nodeData)); };

  const onDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    if (!reactFlowWrapper.current || !reactFlowInstance) return;
    const bounds = reactFlowWrapper.current.getBoundingClientRect();
    const position = reactFlowInstance.screenToFlowPosition({ x: event.clientX - bounds.left, y: event.clientY - bounds.top });
    const data = JSON.parse(event.dataTransfer.getData('application/reactflow'));
    const newNode: Node = { id: `node-${Date.now()}`, type: 'module', position, data: { label: data.label, moduleType: data.type, moduleName: data.moduleName, inputs: data.inputs, outputs: data.outputs } };
    setNodes((nds) => nds.concat(newNode));
  }, [reactFlowInstance, setNodes]);

  const onConnect = useCallback((params: Connection) => { setEdges((eds) => eds.concat({ ...params, type: 'default', markerEnd: { type: MarkerType.ArrowClosed } })); }, [setEdges]);

  const handleSave = useCallback(async () => {
    if (nodes.length === 0) { message.warning('画布上没有节点'); return; }
    setExecuting(true);
    try {
      const flowDefinition: FlowDefinition = { flow_id: `flow_${Date.now()}`, flow_inputs: [], flow_outputs: [], modules: nodes.map(n => ({ id: n.id, module: n.data.moduleName, params: n.data.paramValues || {} })), connections: edges.map(e => ({ from: `${e.source}:${e.sourceHandle || 'out:0'}`, to: `${e.target}:${e.targetHandle || 'in:0'}` })) };
      await createFlow(flowDefinition);
      message.success(`流程已保存！ID: ${flowDefinition.flow_id}`);
    } catch (error: any) { message.error(`保存失败：${error.message}`); }
    finally { setExecuting(false); }
  }, [nodes, edges]);

  const handleRun = useCallback(async () => {
    if (nodes.length === 0) { message.warning('画布上没有节点'); return; }
    setShowInputModal(true);
  }, [nodes]);

  const handleExecuteConfirm = useCallback(async (inputs: Record<string, any>) => {
    setExecuting(true);
    try {
      const flowId = `flow_${Date.now()}`;
      const flowDefinition: FlowDefinition = { flow_id: flowId, flow_inputs: [], flow_outputs: [], modules: nodes.map(n => ({ id: n.id, module: n.data.moduleName })), connections: edges.map(e => ({ from: `${e.source}:${e.sourceHandle || 'out:0'}`, to: `${e.target}:${e.targetHandle || 'in:0'}` })) };
      const result = await executeFlow(flowId, flowDefinition, inputs);
      if (result.success) { message.success('流程执行成功！'); Modal.success({ title: '✅ 执行成功', content: <pre>{JSON.stringify(result.outputs, null, 2)}</pre>, width: 600 }); }
      else { message.error(`执行失败：${result.message}`); }
    } catch (error: any) { message.error(`执行失败：${error.message}`); }
    finally { setExecuting(false); setShowInputModal(false); }
  }, [nodes, edges]);

  return (
    <div style={{ width: '100%', height: '100vh', display: 'flex' }}>
      <div style={{ width: '200px', borderRight: '1px solid #e8e8e8', padding: '16px', background: '#fafafa' }}>
        <h3 style={{ marginBottom: '16px' }}>模块库</h3>
        {moduleTemplates.map((cat, idx) => (<div key={idx} style={{ marginBottom: '24px' }}><h4 style={{ fontSize: '14px', marginBottom: '12px' }}>{cat.category}</h4>{cat.items.map((item, iidx) => (<div key={iidx} draggable onDragStart={(e) => onDragStart(e, item)} style={{ padding: '8px', marginBottom: '8px', background: '#fff', border: '2px solid #1890ff', borderRadius: '4px', cursor: 'grab', fontSize: '13px' }}>{item.label}</div>))}</div>))}
      </div>
      <div style={{ flex: 1 }} ref={reactFlowWrapper}>
        <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect} onDrop={onDrop} onDragOver={(e) => { e.preventDefault(); }} onInit={setReactFlowInstance} nodeTypes={nodeTypes} fitView>
          <Controls />
          <Background />
          <Panel position="top-left" style={{ background: '#fff', padding: '8px', borderRadius: '4px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
            <Space>
              <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleRun} loading={executing}>执行</Button>
              <Button icon={<SaveOutlined />} onClick={handleSave} loading={executing}>保存</Button>
              <Button danger icon={<ClearOutlined />} onClick={() => { setNodes([]); setEdges([]); message.success('画布已清空'); }}>清空</Button>
            </Space>
          </Panel>
        </ReactFlow>
      </div>
      <ExecutionInputDialog open={showInputModal} flowInputs={[]} values={{}} onConfirm={handleExecuteConfirm} onCancel={() => setShowInputModal(false)} />
    </div>
  );
};

export default WorkflowDesigner;
