/** Date helpers — app-wide DISPLAY format is DD-MM-YYYY; the API stores YYYY-MM-DD. */

/** "2026-09-10" (or an ISO timestamp) -> "10-09-2026". Passes through anything unrecognised. */
export const fmtDMY = (key?: string | null): string => {
  if (!key) return "—";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(key);
  return m ? `${m[3]}-${m[2]}-${m[1]}` : key;
};

const pad2 = (n: number) => String(n).padStart(2, "0");

/** ISO timestamp -> "10-09-2026, 06:45 pm" (local time). Date-only strings also work. */
export const fmtDMYTime = (iso?: string | null): string => {
  if (!iso) return "—";
  const d = new Date(iso.length === 10 ? iso + "T00:00:00" : iso);
  if (isNaN(d.getTime())) return fmtDMY(iso);
  const date = `${pad2(d.getDate())}-${pad2(d.getMonth() + 1)}-${d.getFullYear()}`;
  const time = d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  return `${date}, ${time}`;
};

const validYMD = (y: number, mo: number, d: number): string | null => {
  if (mo < 1 || mo > 12 || d < 1 || d > 31) return null;
  const dt = new Date(Date.UTC(y, mo - 1, d));
  if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== mo - 1 || dt.getUTCDate() !== d) return null;
  return `${y}-${pad2(mo)}-${pad2(d)}`;
};

/**
 * Parse a user-typed date into API format "YYYY-MM-DD".
 * Accepts DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY and ISO YYYY-MM-DD.
 * Returns "" for empty input, or null when the text isn't a valid calendar date.
 */
export const toApiDate = (input: string): string | null => {
  const s = (input || "").trim();
  if (!s) return "";
  let m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(s);
  if (m) return validYMD(+m[1], +m[2], +m[3]);
  m = /^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$/.exec(s);
  if (m) return validYMD(+m[3], +m[2], +m[1]);
  return null;
};
