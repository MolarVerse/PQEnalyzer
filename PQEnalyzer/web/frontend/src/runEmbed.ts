const base = typeof window !== "undefined"
  ? window.location.pathname.match(/^\/run-app\/(?:viewer|enalyzer)\/\d+\//)?.[0].slice(0, -1) ?? ""
  : "";

export const runEmbedded = Boolean(base);
export const appApi = (path: string) => base + path;
