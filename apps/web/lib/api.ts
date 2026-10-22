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
  evidence_revision: string;
  eligible_from_ms: number;
  expires_at_ms: number;
  status: string;
  approved?: boolean;
  passer_id?: string;
  receiver_id?: string;
  team_id?: string;
  package_hash?: string;
};
export type Match = {
  session_id: string;
  clock_ms: number;
  duration_ms: number;
  running: boolean;
  speed: number;
  mode: string;
  azure_deployed?: boolean;
  workflow_pending?: boolean;
  story: Story | null;
  stories?: Story[];
  story_status: string;
  overlay: string | null;
  overlay_story_id?: string | null;
  delivered_count: number;
  frame: Frame | null;
  teams: { id: string; name: string; color: string }[];
  players: Player[];
  cursor: number;
};
export type Metrics = {
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
  id: string;
  text: string;
  language: string;
  detail: string;
  focus: string | null;
  clauses?: { id: string; claim_ids: string[]; text: string }[];
};
export type Evidence = {
  cutoff_ms: number;
  frames: { time_ms: number; payload: Frame; message_id: string }[];
  story: {
    id: string;
    revision: number;
    package_hash: string;
    evidence_revision: string;
    metrics: Metrics;
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
export type Recap = {
  title: string;
  through_ms: number;
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
