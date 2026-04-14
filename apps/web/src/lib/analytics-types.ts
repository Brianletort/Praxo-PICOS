export interface NarrativePayload {
  headline: string;
  bullets: string[];
  trend: string;
  sentiment: string;
  available_depth: string[];
}

export interface LearningPlaceholder {
  type: string;
  message: string;
  progress: number;
}

export interface AvailabilityInfo {
  available: string[];
  learning: LearningPlaceholder[];
}

export interface MeetingListItem {
  id: string;
  title: string | null;
  start_time: string | null;
  end_time: string | null;
  duration_minutes: number | null;
  attendee_count: number;
  has_intelligence: boolean;
  intelligence_score: number | null;
  score_dot: "green" | "yellow" | "red" | "none";
  narrative: NarrativePayload;
  detail?: Record<string, unknown>;
}

export interface MeetingListResponse {
  meetings: MeetingListItem[];
  total: number;
  availability: AvailabilityInfo;
}

export interface TopInsight {
  headline: string;
  detail: string;
  actionable: boolean;
}

export interface MeetingDetailResponse {
  id: string;
  title: string | null;
  start_time: string | null;
  end_time: string | null;
  duration_minutes: number | null;
  attendee_ids: string[];
  summary: string | null;
  has_intelligence: boolean;
  intelligence_score: number | null;
  narrative: NarrativePayload;
  top_insights: TopInsight[];
  intelligence?: Record<string, unknown>;
}

export interface PersonDetailResponse {
  id: string;
  name: string;
  email: string | null;
  organization: string | null;
  role: string | null;
  importance_level: number;
  narrative: NarrativePayload;
  top_insights: TopInsight[];
  intelligence?: Record<string, unknown>;
  relationships?: Array<{
    id: string;
    target_id: string;
    type: string;
    attrs: Record<string, unknown>;
  }>;
}

export interface DaySummaryResponse {
  date: string;
  meeting_count: number;
  narrative: NarrativePayload;
  top_insights: TopInsight[];
  people_needing_attention: Array<{ name: string; reason: string }>;
  meetings?: MeetingListItem[];
}

export interface ReadinessResponse {
  counts: {
    meetings: number;
    people: number;
    insights: number;
  };
  readiness: Record<string, AvailabilityInfo>;
}
