export const dynamic = "force-dynamic";
import { BroadcastStage } from "@/components/pitch-broadcast";

export default async function Page({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = await params;
  return (
    <BroadcastStage
      sessionId={sessionId}
      publicBase={process.env.MATCHSENSE_PUBLIC_URL || ""}
    />
  );
}
