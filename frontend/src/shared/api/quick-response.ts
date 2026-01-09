import { apiClient } from "../lib/api-client";
import type { QuickResponse, QuickResponseCreate, QuickResponseScenario } from "../types/api";

export const quickResponseApi = {
  getScenario: async (): Promise<QuickResponseScenario> => {
    return apiClient.get<QuickResponseScenario>("/quick-response/scenario");
  },

  create: async (data: QuickResponseCreate): Promise<QuickResponse> => {
    return apiClient.post<QuickResponse>("/quick-response", data);
  },

  getAll: async (skip = 0, limit = 10): Promise<QuickResponse[]> => {
    return apiClient.get<QuickResponse[]>(
      `/quick-response?skip=${skip}&limit=${limit}`
    );
  },
};


