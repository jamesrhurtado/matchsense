type MatchSenseBrandProps = {
  className?: string;
  markOnly?: boolean;
  dark?: boolean;
};

export function MatchSenseBrand({
  className,
  markOnly = false,
  dark = false,
}: MatchSenseBrandProps) {
  return (
    <span
      className={className}
      aria-label={markOnly ? "MatchSense" : undefined}
      role={markOnly ? "img" : undefined}
      style={{
        alignItems: "center",
        color: dark ? "#f5f2e9" : "#0b191f",
        display: "inline-flex",
        gap: markOnly ? 0 : "0.42em",
        whiteSpace: "nowrap",
      }}
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 42 42"
        style={{
          display: "block",
          flex: "none",
          height: "1.35em",
          width: "1.35em",
        }}
      >
        <path
          d="M5 32V9L21 25 37 9V32"
          fill="none"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="3.5"
        />
        <circle cx="5" cy="9" r="2.5" fill="currentColor" />
        <circle cx="21" cy="25" r="2.5" fill="currentColor" />
        <circle cx="37" cy="9" r="2.5" fill="#a7f3d0" />
      </svg>
      {!markOnly && (
        <span
          style={{
            fontSize: "1em",
            fontWeight: 650,
            letterSpacing: "-0.045em",
          }}
        >
          MatchSense
        </span>
      )}
    </span>
  );
}
