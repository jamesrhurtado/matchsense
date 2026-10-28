import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export const cn = (...values: ClassValue[]) => twMerge(clsx(values));
export type MatchOption = {
  match_id: string;
  label: string;
  duration_ms: number;
  synthetic: true;
};
export type Player = {
  id: string;
  team_id: string;
  name: string;
  number: number;
  role?: "keeper" | "outfield";
};
export type Frame = {
  players: { player_id: string; team_id: string; x_m: number; y_m: number }[];
  ball: { x_m: number; y_m: number } | null;
  controlling_player_id: string | null;
  possession_team_id: string | null;
};
export type Story = {
  id: string;
  revision: number;
  title: string;
  titles?: Record<string, string>;
  family?: string;
  why_now?: Record<string, string>;
  evidence_state?: string;
  notable?: boolean;
  incident_id?: string;
  participants?: Record<string, string | null>;
  related_stories?: Story[];
  selection_reason?: string;
  queue_state?: string;
  evidence_revision: string;
  eligible_from_ms: number;
  occurrence_ms?: number;
  expires_at_ms: number;
  status: string;
  approved?: boolean;
  passer_id?: string;
  receiver_id?: string;
  team_id?: string;
  package_hash?: string;
  editorial_decision?: {
    director: string;
    reviewer: string;
    claim_ids: string[];
    fallback: boolean;
  };
};
export type Match = {
  corrections?: CorrectionNotice[];
  session_id: string;
  score?: Record<string, number>;
  match_state?: {
    score: Record<string, number>;
    period: number;
    period_elapsed_ms: number;
    period_status: string;
    source_status: string;
  };
  approved_possession?: {
    interval: number[];
    text: string;
    story_id: string;
  } | null;
  coverage_enabled?: boolean;
  guided_demo?: boolean;
  session_mode?: "guided" | "live";
  execution?: "ai" | "template";
  live_status?: "ready" | "running" | "complete" | "stopped" | "ai_unavailable";
  last_processed_ms?: number;
  model_identity?: { deployment?: string; version?: string };
  workflow_notices?: { story_id?: string; state: string; at_ms?: number }[];
  workflow_attempts?: {
    story_id: string;
    state: string;
    reason?: string;
    mode: string;
    usage: { calls?: number; total_tokens?: number };
    scheduled_at: string;
    finished_at?: string;
    cutoff_ms: number;
  }[];
  flagship_demo?: boolean;
  clock_ms: number;
  duration_ms: number;
  tracking_hz?: number;
  running: boolean;
  speed: number;
  mode: string;
  azure_deployed?: boolean;
  workflow_pending?: boolean;
  story: Story | null;
  stories?: Story[];
  story_status: string;
  overlay: string | null;
  overlay_question?: string | null;
  overlay_story_id?: string | null;
  overlay_selection_reason?: Record<string, string> | null;
  delivered_count: number;
  frame: Frame | null;
  frame_time_ms?: number | null;
  motion_from_frame?: Frame | null;
  motion_duration_ms?: number | null;
  teams: { id: string; name: string; color: string }[];
  players: Player[];
  cursor: number;
};
export type Metrics = {
  family?: string;
  team_id?: string;
  participants?: Record<string, string | null>;
  window_start_ms?: number;
  window_end_ms?: number;
  facts?: {
    before?: {
      start_ms: number;
      end_ms: number;
      known_ms: number;
      coverage: number;
      mean: number;
    };
    after?: {
      start_ms: number;
      end_ms: number;
      known_ms: number;
      coverage: number;
      mean: number;
    };
    forward_m?: number;
    drop?: number;
    radius_m?: number;
    retained_ms?: number;
    retained_progression_m?: number;
    comparators?: {
      pass_id: string;
      forward_m: number;
      resolution_ms: number;
    }[];
    stands_out?: boolean;
    location?: { x_m: number; y_m: number } | null;
    team_ms?: Record<string, number>;
    percentages?: Record<string, number> | null;
    assigned_ms?: number;
    coverage?: number;
    dead_ms?: number;
    loose_ms?: number;
    unknown_ms?: number;
    score?: Record<string, number>;
    score_before?: Record<string, number>;
    previous_team_id?: string | null;
    new_team_id?: string;
  };
  forward_pass_m?: number;
  release_ms?: number;
  reception_ms?: number;
  reception_zone?: string;
  context?: {
    status: string;
    relation: string;
    comparators: {
      pass_id: string;
      resolution_ms: number;
      forward_m: number;
    }[];
  };
  pressure_opponents_max: number;
  pressure_radius_m: number;
  pressure_samples: number;
  bypassed_count: number;
  bypassed_player_ids: string[];
  progression_m: number;
  retention_window_ms: number;
  coverage: number;
  source_message_ids: string[];
  limitations: string[];
  pass_start: { x_m: number; y_m: number };
  pass_end: { x_m: number; y_m: number };
  passer_id: string;
  receiver_id: string;
  pressure_window_ms?: [number, number];
  retention_confirmed_at_ms?: number;
};
export type Variant = {
  story_id?: string;
  revision?: number;
  id: string;
  text: string;
  language: string;
  detail: string;
  focus: string | null;
  clauses?: { id: string; claim_ids: string[]; text: string }[];
};
export type Evidence = {
  related_stories?: {
    id: string;
    revision: number;
    family: string;
    texts: Record<string, string>;
    source_message_ids: string[];
    evidence_revision: string;
  }[];
  sources?: {
    message_id: string;
    timeline_ms?: number;
    available_at_ms?: number;
    kind?: string;
    revision?: number;
    hash?: string;
  }[];
  cutoff_ms: number;
  frames: { time_ms: number; payload: Frame; message_id: string }[];
  story: {
    id: string;
    revision: number;
    package_hash: string;
    evidence_revision: string;
    metrics: Metrics;
    entities?: { players: Player[]; teams: { id: string; name: string }[] };
    narrative_plan?: { angle: string };
    variants: Variant[];
    mode: string;
    review: {
      status: string;
      reason: string;
      proposed_text: string | null;
      revised_text: string;
      cycles: number;
    };
    workflow_ms: number;
    model_calls?: number;
    model_tokens?: number;
    trace: {
      role: string;
      action: string;
      status: string;
      elapsed_ms: number;
    }[];
  };
};
export type CorrectionNotice = {
  notice_id: string;
  story_id: string;
  at_ms: number;
  story_at_ms: number;
  family: string;
  kind: "source_changed" | "producer_retracted";
  text: string;
};
export type Recap = {
  title: string;
  from_ms?: number;
  evaluated_at_ms?: number;
  corrections?: CorrectionNotice[];
  correction_count?: number;
  through_ms: number;
  truncated?: boolean;
  timeline_count?: number;
  match_state?: Match["match_state"];
  moments: {
    story_id: string;
    revision: number;
    title: string;
    text: string;
    at_ms: number;
    archived: boolean;
    similar_moments: { story_id: string; revision: number; at_ms: number }[];
  }[];
};
export const timecode = (ms: number) =>
  `${Math.floor(ms / 60000)
    .toString()
    .padStart(
      2,
      "0",
    )}:${Math.floor(ms / 1000) % 60 < 10 ? "0" : ""}${Math.floor(ms / 1000) % 60}`;
export function token() {
  return typeof window !== "undefined"
    ? sessionStorage.getItem("why-now-token") || ""
    : "";
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
  protectedCall = false,
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(protectedCall ? { "X-Producer-Token": token() } : {}),
      ...options.headers,
    },
    cache: "no-store",
    signal: options.signal ?? AbortSignal.timeout(90_000),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      body.detail?.code?.replaceAll("_", " ") ||
        `Request failed (${response.status})`,
    );
  }
  return response.json();
}
