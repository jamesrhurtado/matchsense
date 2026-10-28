import { cp, mkdir, rm } from "node:fs/promises";
import { join } from "node:path";

const webRoot = process.cwd();
const standaloneRoot = join(webRoot, ".next", "standalone");
const staticSource = join(webRoot, ".next", "static");
const publicSource = join(webRoot, "public");
const staticTarget = join(standaloneRoot, ".next", "static");
const publicTarget = join(standaloneRoot, "public");

await mkdir(join(standaloneRoot, ".next"), { recursive: true });
await rm(staticTarget, { recursive: true, force: true });
await rm(publicTarget, { recursive: true, force: true });
await cp(staticSource, staticTarget, { recursive: true });
await cp(publicSource, publicTarget, { recursive: true });
