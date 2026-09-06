import {
  View, Text, StyleSheet, Pressable, ScrollView, ActivityIndicator, Platform, Linking,
} from "react-native";
import { useCallback, useEffect, useState } from "react";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter, useFocusEffect } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

import { theme } from "@/src/lib/theme";
import { API } from "@/src/lib/api";
import { storage } from "@/src/utils/storage";
import { TOKEN_KEY } from "@/src/lib/api";
import { useAuth } from "@/src/lib/auth";

const BACKEND = process.env.EXPO_PUBLIC_BACKEND_URL;

type Pnl = {
  since: string; days: number; revenue: number; cogs: number; gross_profit: number;
  expenses: number; net_profit: number; sales_count: number; invoice_count: number; expense_count: number;
};

type ProfitRow = {
  key: string; sales_revenue: number; invoice_revenue: number;
  revenue: number; cogs: number; gross_profit: number; expenses: number; net_profit: number;
  sales_count: number; invoice_count: number; expense_count: number;
};

type ProfitResp = {
  rows: ProfitRow[];
  totals: { revenue: number; cogs: number; gross_profit: number; expenses: number; net_profit: number };
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const monthLabel = (k: string) => {
  const [y, m] = k.split("-");
  const mi = parseInt(m, 10) - 1;
  return `${MONTHS[mi] || m} ${y}`;
};
const dayLabel = (k: string) => {
  const [, m, d] = k.split("-");
  return `${parseInt(d, 10)} ${MONTHS[parseInt(m, 10) - 1] || ""}`;
};

async function auth<T>(path: string): Promise<T> {
  const t = await storage.secureGet(TOKEN_KEY, "");
  const res = await fetch(`${API}${path}`, { headers: { Authorization: `Bearer ${t}` } });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export default function Reports() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const [pnl, setPnl] = useState<Pnl | null>(null);
  const [daily, setDaily] = useState<ProfitResp | null>(null);
  const [monthly, setMonthly] = useState<ProfitResp | null>(null);
  const [months, setMonths] = useState(12);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string>("");

  const load = useCallback(async () => {
    try {
      const [p, d, m] = await Promise.all([
        auth<Pnl>(`/stats/pnl`),
        auth<ProfitResp>(`/stats/profit-daily?days=30`),
        auth<ProfitResp>(`/stats/profit-monthly?months=${months}`),
      ]);
      setPnl(p); setDaily(d); setMonthly(m);
    }
    catch (e) { console.log(e); }
    finally { setLoading(false); }
  }, [months]);

  useEffect(() => { load(); }, [load]);
  useFocusEffect(useCallback(() => { load(); }, [load]));

  const openDownload = async (url: string, filename: string) => {
    if (Platform.OS === "web") {
      // trigger browser download
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
    } else {
      await Linking.openURL(url);
    }
  };

  const download = async (kind: "sales" | "expenses" | "pnl") => {
    setBusy(kind);
    try {
      const { token } = await auth<{ token: string }>(`/reports/token?kind=${kind}`);
      await openDownload(`${BACKEND}/api/reports/${kind}.xlsx?token=${token}`, `${kind}.xlsx`);
    } catch (e: any) {
      console.log(e);
    } finally {
      setBusy("");
    }
  };

  // Full data backup — every collection (customers, sales, invoices, receipts, collections, attendance, users …)
  const backup = async (format: "xlsx" | "json") => {
    setBusy(`backup-${format}`);
    try {
      const { token } = await auth<{ token: string }>(`/admin/backup/token`);
      const stamp = new Date().toISOString().slice(0, 10);
      await openDownload(`${BACKEND}/api/admin/backup.${format}?token=${token}`, `backup_${stamp}.${format}`);
    } catch (e: any) {
      console.log(e);
    } finally {
      setBusy("");
    }
  };

  const fmt = (n: number) => "₹" + Math.round(n).toLocaleString("en-IN");

  if (user?.role !== "admin") {
    return (
      <View style={[styles.container, { paddingTop: insets.top, alignItems: "center", justifyContent: "center" }]}>
        <Ionicons name="lock-closed" size={40} color={theme.color.muted} />
        <Text style={styles.deniedTitle}>Admin only</Text>
        <Pressable style={styles.backBtn} onPress={() => router.back()}>
          <Text style={styles.backBtnText}>Go back</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]} testID="reports-screen">
      <View style={styles.hdr}>
        <Pressable onPress={() => router.back()} style={styles.backIcon}>
          <Ionicons name="chevron-back" size={22} color={theme.color.onSurface} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={styles.hdrTitle}>Reports</Text>
          <Text style={styles.hdrSub}>Last 30 days · download Excel</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={{ padding: theme.space.lg, paddingBottom: 64 }}>
        {loading || !pnl ? (
          <ActivityIndicator color={theme.color.brand} style={{ marginTop: 32 }} />
        ) : (
          <>
            <View style={styles.pnlCard}>
              <Text style={styles.pnlLabel}>NET PROFIT · LAST {pnl.days} DAYS</Text>
              <Text style={[styles.pnlNet, pnl.net_profit < 0 && { color: theme.color.error }]}>
                {fmt(pnl.net_profit)}
              </Text>
              <View style={styles.pnlRow}>
                <PnlLine label="Revenue" value={fmt(pnl.revenue)} count={`${pnl.sales_count} sales · ${pnl.invoice_count} invoices`} />
                <PnlLine label="COGS" value={"−" + fmt(pnl.cogs)} count="product cost" />
              </View>
              <View style={styles.divider} />
              <View style={styles.pnlRow}>
                <PnlLine label="Gross profit" value={fmt(pnl.gross_profit)} count="revenue − cogs" />
                <PnlLine label="Expenses" value={"−" + fmt(pnl.expenses)} count={`${pnl.expense_count} logged`} />
              </View>
            </View>

            <Text style={styles.section}>PER-DAY PROFIT · LAST 30 DAYS</Text>
            <View style={styles.group}>
              {daily && daily.rows.length > 0 ? (
                daily.rows.map((r) => (
                  <View key={r.key} style={styles.dayRow} testID={`profit-day-${r.key}`}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.dayDate}>{dayLabel(r.key)}</Text>
                      <Text style={styles.dayMeta}>
                        Rev {fmt(r.revenue)} · Cost {fmt(r.cogs)} · Exp {fmt(r.expenses)}
                      </Text>
                    </View>
                    <Text style={[styles.dayNet, r.net_profit < 0 && { color: theme.color.error }]}>
                      {fmt(r.net_profit)}
                    </Text>
                  </View>
                ))
              ) : (
                <View style={styles.emptyRow}><Text style={styles.emptyRowText}>No sales, invoices or expenses yet.</Text></View>
              )}
            </View>

            <Text style={styles.section}>MONTHLY PROFIT & EXPENSE</Text>
            {monthly && monthly.rows.length > 0 ? (
              <>
                {monthly.rows.map((r) => (
                  <View key={r.key} style={styles.monthCard} testID={`profit-month-${r.key}`}>
                    <View style={styles.monthHead}>
                      <Text style={styles.monthTitle}>{monthLabel(r.key)}</Text>
                      <Text style={[styles.monthNet, r.net_profit < 0 && { color: theme.color.error }]}>
                        {fmt(r.net_profit)}
                      </Text>
                    </View>
                    <Text style={styles.monthNetLabel}>Net profit</Text>
                    <View style={styles.monthGrid}>
                      <MiniStat label="Revenue" value={fmt(r.revenue)} />
                      <MiniStat label="Product cost" value={fmt(r.cogs)} />
                      <MiniStat label="Expenses" value={fmt(r.expenses)} />
                    </View>
                    <Text style={styles.monthSub}>
                      {r.sales_count} sales · {r.invoice_count} invoices · {r.expense_count} expenses
                    </Text>
                  </View>
                ))}
                {monthly.rows.length >= months ? (
                  <Pressable onPress={() => setMonths((m) => m + 12)} style={styles.moreBtn} testID="load-more-months">
                    <Ionicons name="chevron-down" size={16} color={theme.color.brand} />
                    <Text style={styles.moreBtnText}>Show earlier months</Text>
                  </Pressable>
                ) : null}
              </>
            ) : (
              <View style={styles.group}>
                <View style={styles.emptyRow}><Text style={styles.emptyRowText}>No monthly data yet.</Text></View>
              </View>
            )}

            <Text style={styles.section}>DOWNLOAD</Text>
            <View style={styles.group}>
              <DownloadRow icon="cash-outline" label="Sales report" hint="Every sale with profit column" busy={busy === "sales"} onPress={() => download("sales")} testID="download-sales" />
              <DownloadRow icon="receipt-outline" label="Expenses report" hint="All expense entries" busy={busy === "expenses"} onPress={() => download("expenses")} testID="download-expenses" />
              <DownloadRow icon="stats-chart-outline" label="P&L report" hint="Day-by-day profit/loss + totals" busy={busy === "pnl"} onPress={() => download("pnl")} testID="download-pnl" />
            </View>

            <Text style={styles.section}>BACKUP ALL DATA</Text>
            <View style={styles.group}>
              <DownloadRow icon="server-outline" label="Backup (Excel)" hint="One sheet per collection — customers, sales, invoices, receipts, collections, cash verifications, attendance, users, settings…" busy={busy === "backup-xlsx"} onPress={() => backup("xlsx")} testID="backup-xlsx" />
              <DownloadRow icon="code-download-outline" label="Backup (JSON, restore-ready)" hint="Exact copy of every record. Keep it private — it contains account data." busy={busy === "backup-json"} onPress={() => backup("json")} testID="backup-json" />
            </View>
            <Text style={styles.backupHint}>Tip: also use “Save to GitHub” for the code. Run a backup at least weekly and keep the files somewhere safe (Drive / laptop).</Text>
          </>
        )}
      </ScrollView>
    </View>
  );
}

function PnlLine({ label, value, count }: { label: string; value: string; count: string }) {
  return (
    <View style={{ flex: 1 }}>
      <Text style={styles.pnlLineLabel}>{label}</Text>
      <Text style={styles.pnlLineValue}>{value}</Text>
      <Text style={styles.pnlLineCount}>{count}</Text>
    </View>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.miniStat}>
      <Text style={styles.miniStatLabel}>{label}</Text>
      <Text style={styles.miniStatValue}>{value}</Text>
    </View>
  );
}

function DownloadRow({ icon, label, hint, onPress, busy, testID }: { icon: keyof typeof Ionicons.glyphMap; label: string; hint: string; onPress: () => void; busy: boolean; testID?: string }) {
  return (
    <Pressable onPress={onPress} disabled={busy} style={({ pressed }) => [styles.row, pressed && { backgroundColor: theme.color.surfaceTertiary }]} testID={testID}>
      <View style={styles.iconWrap}>
        {busy ? <ActivityIndicator color={theme.color.brand} /> : <Ionicons name={icon} size={20} color={theme.color.brand} />}
      </View>
      <View style={{ flex: 1 }}>
        <Text style={styles.rowLabel}>{label}</Text>
        <Text style={styles.rowHint}>{hint}</Text>
      </View>
      <Ionicons name="download-outline" size={18} color={theme.color.muted} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.color.surface },
  hdr: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingHorizontal: theme.space.md, paddingVertical: theme.space.md,
    backgroundColor: theme.color.surfaceSecondary, borderBottomWidth: 1, borderBottomColor: theme.color.border,
  },
  backIcon: { width: 32, height: 32, alignItems: "center", justifyContent: "center" },
  hdrTitle: { fontSize: theme.font.scale.xl, fontWeight: "800", color: theme.color.onSurface },
  hdrSub: { fontSize: theme.font.scale.sm, color: theme.color.muted, marginTop: 2 },
  pnlCard: {
    backgroundColor: theme.color.surfaceInverse, borderRadius: theme.radius.lg,
    padding: theme.space.xl,
  },
  pnlLabel: { color: theme.color.borderStrong, fontSize: 11, fontWeight: "700", letterSpacing: 1.5 },
  pnlNet: { color: theme.color.success, fontSize: 40, fontWeight: "800", marginTop: 6, letterSpacing: -1 },
  pnlRow: { flexDirection: "row", gap: theme.space.md, marginTop: theme.space.lg },
  divider: { height: 1, backgroundColor: "rgba(255,255,255,0.15)", marginVertical: theme.space.md },
  pnlLineLabel: { color: theme.color.borderStrong, fontSize: 11, fontWeight: "700", letterSpacing: 1 },
  pnlLineValue: { color: "#fff", fontSize: 18, fontWeight: "800", marginTop: 4 },
  pnlLineCount: { color: theme.color.borderStrong, fontSize: 11, marginTop: 2, fontWeight: "600" },
  section: {
    fontSize: 11, letterSpacing: 1, color: theme.color.muted, fontWeight: "700",
    marginBottom: theme.space.sm, marginTop: theme.space.xl,
  },
  group: { backgroundColor: theme.color.surfaceSecondary, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.color.border, overflow: "hidden" },
  row: { flexDirection: "row", alignItems: "center", padding: theme.space.md, borderBottomWidth: 1, borderBottomColor: theme.color.border },
  iconWrap: { width: 36, height: 36, borderRadius: 10, alignItems: "center", justifyContent: "center", marginRight: theme.space.md, backgroundColor: theme.color.brandTertiary },
  rowLabel: { fontSize: theme.font.scale.lg, fontWeight: "600", color: theme.color.onSurface },
  rowHint: { fontSize: theme.font.scale.sm, color: theme.color.muted, marginTop: 2 },
  backupHint: { fontSize: 11, color: theme.color.muted, marginTop: theme.space.sm, lineHeight: 16 },
  dayRow: { flexDirection: "row", alignItems: "center", padding: theme.space.md, borderBottomWidth: 1, borderBottomColor: theme.color.border },
  dayDate: { fontSize: 14, fontWeight: "800", color: theme.color.onSurface },
  dayMeta: { fontSize: 11, color: theme.color.muted, marginTop: 2 },
  dayNet: { fontSize: 16, fontWeight: "900", color: theme.color.success, marginLeft: theme.space.md },
  emptyRow: { padding: theme.space.lg, alignItems: "center" },
  emptyRowText: { fontSize: 12, color: theme.color.muted },
  monthCard: {
    backgroundColor: theme.color.surfaceSecondary, borderRadius: theme.radius.md,
    borderWidth: 1, borderColor: theme.color.border, padding: theme.space.md, marginBottom: theme.space.sm,
  },
  monthHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  monthTitle: { fontSize: 16, fontWeight: "800", color: theme.color.onSurface },
  monthNet: { fontSize: 20, fontWeight: "900", color: theme.color.success },
  monthNetLabel: { fontSize: 10, color: theme.color.muted, fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.5, textAlign: "right", marginTop: -2 },
  monthGrid: { flexDirection: "row", gap: 8, marginTop: theme.space.md },
  miniStat: { flex: 1, backgroundColor: theme.color.surface, borderRadius: theme.radius.sm, borderWidth: 1, borderColor: theme.color.border, padding: 8 },
  miniStatLabel: { fontSize: 10, color: theme.color.muted, fontWeight: "700" },
  miniStatValue: { fontSize: 14, fontWeight: "800", color: theme.color.onSurface, marginTop: 2 },
  monthSub: { fontSize: 11, color: theme.color.muted, marginTop: theme.space.sm, fontWeight: "600" },
  moreBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 4,
    paddingVertical: theme.space.md, borderRadius: theme.radius.md,
    borderWidth: 1, borderColor: theme.color.border, borderStyle: "dashed", marginTop: 4,
  },
  moreBtnText: { fontSize: 13, fontWeight: "800", color: theme.color.brand },
  deniedTitle: { marginTop: theme.space.md, fontSize: 20, fontWeight: "800", color: theme.color.onSurface },
  backBtn: { marginTop: theme.space.lg, paddingHorizontal: theme.space.xl, paddingVertical: theme.space.md, borderRadius: theme.radius.md, backgroundColor: theme.color.brand },
  backBtnText: { color: theme.color.onBrand, fontWeight: "700" },
});
