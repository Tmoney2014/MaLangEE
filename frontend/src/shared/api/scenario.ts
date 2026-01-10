import { apiClient } from "../lib/api-client";
import type { Scenario, ScenarioCreate, ScenarioType } from "../types/api";

export const scenarioApi = {
  getTypes: async (): Promise<ScenarioType[]> => {
    return apiClient.get<ScenarioType[]>("/scenario/types");
  },

  create: async (data: ScenarioCreate): Promise<Scenario> => {
    return apiClient.post<Scenario>("/scenario", data);
  },

  addMessage: async (scenarioId: number, message: string): Promise<Scenario> => {
    return apiClient.post<Scenario>(`/scenario/${scenarioId}/message`, {
      message,
    });
  },

  getAll: async (skip = 0, limit = 10): Promise<Scenario[]> => {
    return apiClient.get<Scenario[]>(`/scenario?skip=${skip}&limit=${limit}`);
  },

  getById: async (scenarioId: number): Promise<Scenario> => {
    return apiClient.get<Scenario>(`/scenario/${scenarioId}`);
  },
};


