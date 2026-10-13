import { relayToAiService } from "@/lib/ai-service/relay";

type Ctx = { params: Promise<{ path: string[] }> };

async function handle(request: Request, ctx: Ctx): Promise<Response> {
  const { path } = await ctx.params;
  const upstreamPath = `/api/v1/${path.join("/")}`;
  return relayToAiService(request, upstreamPath);
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
