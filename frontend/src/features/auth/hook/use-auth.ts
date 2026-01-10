"use client";

import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { tokenStorage } from "../model";
import { useCurrentUser } from "../api";

/**
 * 인증 상태 및 액션을 제공하는 통합 훅
 */
export function useAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: user, isLoading, isError, refetch } = useCurrentUser();

  const isAuthenticated = !!user && !isError;

  const logout = useCallback(() => {
    tokenStorage.remove();
    queryClient.clear();
    router.push("/auth/login");
  }, [queryClient, router]);

  const refreshUser = useCallback(() => {
    return refetch();
  }, [refetch]);

  return {
    user,
    isAuthenticated,
    isLoading,
    isError,
    logout,
    refreshUser,
  };
}
