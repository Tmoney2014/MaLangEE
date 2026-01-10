"use client";

import { useState, useEffect, useRef } from "react";
import { authApi } from "../api";

interface UseDuplicateCheckOptions {
  /** 디바운스 지연 시간 (ms) */
  debounceMs?: number;
  /** 최소 입력 길이 */
  minLength?: number;
}

interface UseDuplicateCheckResult {
  /** 에러 메시지 (null이면 에러 없음) */
  error: string | null;
  /** 확인 중 여부 */
  isChecking: boolean;
  /** 사용 가능 여부 (null이면 아직 확인 안됨) */
  isAvailable: boolean | null;
}

/**
 * 로그인 ID 중복 확인 훅
 */
export function useLoginIdCheck(
  value: string,
  options: UseDuplicateCheckOptions = {}
): UseDuplicateCheckResult {
  const { debounceMs = 500, minLength = 1 } = options;

  const [error, setError] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [isAvailable, setIsAvailable] = useState<boolean | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    // 이전 요청 취소
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // 값이 없거나 최소 길이 미달이면 초기화
    if (!value || value.length < minLength) {
      setError(null);
      setIsAvailable(null);
      setIsChecking(false);
      return;
    }

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const timer = setTimeout(async () => {
      if (abortController.signal.aborted) return;

      setIsChecking(true);
      try {
        const result = await authApi.checkLoginId(value);
        if (abortController.signal.aborted) return;

        setIsAvailable(result.is_available);
        setError(result.is_available ? null : "이미 사용중인 아이디입니다");
      } catch {
        if (abortController.signal.aborted) return;
        setError("아이디 확인 중 오류가 발생했습니다");
        setIsAvailable(null);
      } finally {
        if (!abortController.signal.aborted) {
          setIsChecking(false);
        }
      }
    }, debounceMs);

    return () => {
      clearTimeout(timer);
      abortController.abort();
    };
  }, [value, debounceMs, minLength]);

  return { error, isChecking, isAvailable };
}

/**
 * 닉네임 중복 확인 훅
 */
export function useNicknameCheck(
  value: string,
  options: UseDuplicateCheckOptions = {}
): UseDuplicateCheckResult {
  const { debounceMs = 500, minLength = 1 } = options;

  const [error, setError] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [isAvailable, setIsAvailable] = useState<boolean | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    if (!value || value.length < minLength) {
      setError(null);
      setIsAvailable(null);
      setIsChecking(false);
      return;
    }

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const timer = setTimeout(async () => {
      if (abortController.signal.aborted) return;

      setIsChecking(true);
      try {
        const result = await authApi.checkNickname(value);
        if (abortController.signal.aborted) return;

        setIsAvailable(result.is_available);
        setError(result.is_available ? null : "이미 사용중인 닉네임입니다");
      } catch {
        if (abortController.signal.aborted) return;
        setError("닉네임 확인 중 오류가 발생했습니다");
        setIsAvailable(null);
      } finally {
        if (!abortController.signal.aborted) {
          setIsChecking(false);
        }
      }
    }, debounceMs);

    return () => {
      clearTimeout(timer);
      abortController.abort();
    };
  }, [value, debounceMs, minLength]);

  return { error, isChecking, isAvailable };
}
