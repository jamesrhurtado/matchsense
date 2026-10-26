import { cn } from "@/lib/api";
export function Button({
  className,
  tone = "secondary",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  tone?: "primary" | "secondary" | "danger";
}) {
  return (
    <button
      className={cn(
        "inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700",
        tone === "primary"
          ? "bg-emerald-800 text-white shadow-sm hover:bg-emerald-900 hover:shadow"
          : tone === "danger"
            ? "border border-red-200 bg-white text-red-700 hover:bg-red-50"
            : "border border-stone-300 bg-white text-stone-700 shadow-sm hover:border-emerald-300 hover:bg-emerald-50/50",
        className,
      )}
      {...props}
    />
  );
}
export function Tag({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-stone-200 bg-stone-100 px-2.5 py-1 text-xs font-semibold text-stone-700",
        className,
      )}
    >
      {children}
    </span>
  );
}
export function Card({
  children,
  className,
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  return (
    <section
      className={cn(
        "rounded-2xl border border-[#d9e3dd] bg-white shadow-[0_1px_2px_rgba(18,47,39,0.04),0_14px_34px_-26px_rgba(18,47,39,0.24)]",
        className,
      )}
      {...props}
    >
      {children}
    </section>
  );
}
