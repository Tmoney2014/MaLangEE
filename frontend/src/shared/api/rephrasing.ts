import { apiClient } from "../lib/api-client";
import type { Rephrasing, RephrasingCreate, RephrasingSentence } from "../types/api";

export const rephrasingApi = {
  getSentence: async (): Promise<RephrasingSentence> => {
    return apiClient.get<RephrasingSentence>("/rephrasing/sentence");
  },

  create: async (data: RephrasingCreate): Promise<Rephrasing> => {
    return apiClient.post<Rephrasing>("/rephrasing", data);
  },

  getAll: async (skip = 0, limit = 10): Promise<Rephrasing[]> => {
    return apiClient.get<Rephrasing[]>(
      `/rephrasing?skip=${skip}&limit=${limit}`
    );
  },
};


