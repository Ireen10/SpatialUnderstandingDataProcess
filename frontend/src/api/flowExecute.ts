import axios from 'axios';

const API_BASE = '/api/v1';

export interface FlowDefinition {
  flow_id: string;
  flow_inputs: Array<{ port: string; type: string }>;
  flow_outputs: Array<{ port: string; type: string }>;
  modules: Array<{ id: string; module: string; params?: any }>;
  connections: Array<{ from: string; to: string }>;
}

export interface ExecuteFlowRequest {
  flow_id: string;
  flow_definition: FlowDefinition;
  inputs: Record<string, any>;
}

export interface ExecuteFlowResponse {
  success: boolean;
  flow_id: string;
  outputs: Record<string, any>;
  message: string;
}

export const executeFlow = async (flowId: string, flowDefinition: FlowDefinition, inputs: Record<string, any>): Promise<ExecuteFlowResponse> => {
  const response = await axios.post<ExecuteFlowResponse>(`${API_BASE}/flows/execute`, {
    flow_id: flowId,
    flow_definition: flowDefinition,
    inputs: inputs,
  });
  return response.data;
};

export const createFlow = async (flowDefinition: FlowDefinition) => {
  const response = await axios.post(`${API_BASE}/flows/create`, flowDefinition);
  return response.data;
};

export const getFlow = async (flowId: string) => {
  const response = await axios.get(`${API_BASE}/flows/${flowId}`);
  return response.data;
};

export const listFlows = async () => {
  const response = await axios.get(`${API_BASE}/flows/list`);
  return response.data;
};

export const deleteFlow = async (flowId: string) => {
  const response = await axios.delete(`${API_BASE}/flows/${flowId}`);
  return response.data;
};

export default { executeFlow, createFlow, getFlow, listFlows, deleteFlow };
