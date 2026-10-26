import { BroadcastOverlay } from "@/components/pitch-broadcast";

export default async function Page({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = await params;
  return <BroadcastOverlay sessionId={sessionId} />;
}
