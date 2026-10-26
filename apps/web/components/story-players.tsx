import { Player, Story } from "@/lib/api";

const ROLE_LABELS: Record<string, { en: string; es: string }> = {
  passer: { en: "Passer", es: "Pasador" },
  receiver: { en: "Receiver", es: "Receptor" },
  scorer: { en: "Scorer", es: "Goleador" },
  shooter: { en: "Shooter", es: "Rematador" },
  actor: { en: "Player", es: "Jugador" },
};

/** Show only players whose roles are explicitly attached to this story. */
export function StoryPlayers({
  story,
  players,
  teamNames,
  language = "en",
}: {
  story: Story;
  players: Player[];
  teamNames?: Record<string, string>;
  language?: string;
}) {
  const es = language === "es";
  const roles: [string, string][] = [
    ...(story.passer_id
      ? [["passer", story.passer_id] as [string, string]]
      : []),
    ...(story.receiver_id
      ? [["receiver", story.receiver_id] as [string, string]]
      : []),
    ...(Object.entries(story.participants || {}).filter(
      ([role, id]) =>
        Boolean(id) &&
        !["passer", "receiver"].includes(role) &&
        Boolean(ROLE_LABELS[role]),
    ) as [string, string][]),
  ];
  const seen = new Set<string>();
  const identified = roles.flatMap(([role, id]) => {
    const player = players.find((item) => item.id === id);
    if (!player || seen.has(id)) return [];
    seen.add(id);
    return [{ player, role }];
  });
  if (!identified.length) return null;

  return (
    <div
      className="mt-3 flex flex-wrap items-center gap-2"
      aria-label={es ? "Jugadores identificados" : "Players in this story"}
    >
      {identified.map(({ player, role }, index) => (
        <span
          key={`${role}:${player.id}`}
          className="inline-flex min-h-8 items-center gap-1.5 rounded-full border border-stone-200 bg-white/80 px-3 text-xs text-stone-700"
        >
          <span className="font-semibold">
            #{player.number} {player.name}
          </span>
          <span className="text-stone-500">
            {teamNames?.[player.team_id] || player.team_id} ·{" "}
            {ROLE_LABELS[role]?.[es ? "es" : "en"] ||
              (es ? "Jugador" : "Player")}
          </span>
          {role === "passer" && story.receiver_id && index === 0 && (
            <span aria-hidden="true" className="ml-0.5 text-stone-400">
              →
            </span>
          )}
        </span>
      ))}
    </div>
  );
}
