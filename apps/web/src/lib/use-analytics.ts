"use client";

import { useEffect, useState, useCallback } from "react";
import type {
  MeetingListResponse,
  MeetingDetailResponse,
  PersonDetailResponse,
  DaySummaryResponse,
  ReadinessResponse,
} from "./analytics-types";

const BASE = "";

async function fetchAnalytics<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(`Analytics API error ${res.status}`);
  return res.json() as Promise<T>;
}

export function useDaySummary(date?: string) {
  const [data, setData] = useState<DaySummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = date ? `?date=${date}` : "";
    fetchAnalytics<DaySummaryResponse>(`/api/analytics/day${params}`)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [date]);

  return { data, loading };
}

export function useMeetings(rangeWeeks = 4, detail: "simple" | "full" = "simple") {
  const [data, setData] = useState<MeetingListResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics<MeetingListResponse>(
      `/api/analytics/meetings?range_weeks=${rangeWeeks}&detail=${detail}`
    )
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [rangeWeeks, detail]);

  return { data, loading };
}

export function useMeeting(meetingId: string, detail: "simple" | "full" = "simple") {
  const [data, setData] = useState<MeetingDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics<MeetingDetailResponse>(
      `/api/analytics/meetings/${meetingId}?detail=${detail}`
    )
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [meetingId, detail]);

  return { data, loading };
}

export function usePerson(personId: string, detail: "simple" | "full" = "simple") {
  const [data, setData] = useState<PersonDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics<PersonDetailResponse>(
      `/api/analytics/person/${personId}?detail=${detail}`
    )
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [personId, detail]);

  return { data, loading };
}

export function useReadiness() {
  const [data, setData] = useState<ReadinessResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics<ReadinessResponse>("/api/analytics/readiness")
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading };
}
