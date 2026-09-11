import { View, Text, StyleSheet, Pressable, ScrollView, ActivityIndicator, RefreshControl } from "react-native";
import { useCallback, useEffect, useState } from "react";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter, useFocusEffect } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

import { theme } from "@/src/lib/theme";
import { api, STATUS_LABEL, STATUS_COLOR, MyReport, ReportBucket } from "@/src/lib/api";
import { useAuth } from "@/src/lib/auth";

type Period = "weekly" | "monthly";

const fmtMoney = (n: number) => "₹" + Math.round(n || 0).toLocaleString("en-IN");
// Order that reads well; only non-zero shown
const STATUS_ORDER = ["done", "interested", "callback", "no_answer", "not_interested", "pending"];

export default function MyReportScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [period, setPeriod] = useState<Period>("weekly");
  const [data, setData] = useState<MyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const r = await api.myReport(8, 6);
      setData(r);
    } catch (e) {
      console.log("my-report err", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);
  useFocusEffect(useCallback(() => { load(); }, [load]));

  const rows: ReportBucket[] = (data ? data[period] : []) || [];

  // Totals across the shown buckets
  const totalCalls = rows.reduce((a, b) => a + (b.calls || 0), 0);
  const totalSales = rows.reduce((a, b) => a + (b.sales_count || 0), 0);
  const totalInvoices = rows.reduce((a, b) => a + (b.invoices_count || 0), 0);
  const totalRevenue = rows.reduce((a, b) => a + (b.revenue || 0), 0);
  const totalProfit = rows.reduce((a, b) => a + (b.profit || 0), 0);

  return (
    <View style={[styles.container, { paddingTop: insets.top }]} testID="my-report-screen">
      <View style={styles.hdr}>
        <Pressable onPress={() => router.back()} style={styles.backIcon}>
          <Ionicons name="chevron-back" size={22} color={theme.color.onSurface} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={styles.hdrTitle}>My report</Text>
          <Text style={styles.hdrSub}>Your sales & calls · {user?.display_name || user?.username}</Text>
        </View>
      </View>

      {/* Weekly / Monthly toggle */}
      <View style={styles.toggleWrap}>
        <Pressable
          onPress={() => setPeriod("weekly")}
          style={[styles.toggleBtn, period === "weekly" && styles.toggleBtnActive]}
          testID="toggle-weekly"
        >
          <Text style={[styles.toggleText, period === "weekly" && styles.toggleTextActive]}>Weekly</Text>
        </Pressable>
        <Pressable
          onPress={() => setPeriod("monthly")}
          style={[styles.toggleBtn, period === "monthly" && styles.toggleBtnActive]}
          testID="toggle-monthly"
        >
          <Text style={[styles.toggleText, period === "monthly" && styles.toggleTextActive]}>Monthly</Text>
        </Pressable>
      </View>

      {loading ? (
        <View style={styles.center}><ActivityIndicator color={theme.color.brand} /></View>
      ) : (
        <ScrollView
          contentContainerStyle={{ padding: theme.space.lg, paddingBottom: 64 }}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
        >
          {/* Summary strip */}
          <View style={styles.summaryCard}>
            <Text style={styles.summaryLabel}>
              {period === "weekly" ? "LAST 8 WEEKS" : "LAST 6 MONTHS"}
            </Text>
            <View style={styles.summaryRow}>
              <SummaryStat icon="call" label="Calls" value={String(totalCalls)} />
              <SummaryStat icon="cart" label="Sales" value={String(totalSales)} />
              <SummaryStat icon="document-text" label="Invoices" value={String(totalInvoices)} />
              <SummaryStat icon="cash" label="Revenue" value={fmtMoney(totalRevenue)} />
              {isAdmin ? (
                <SummaryStat icon="trending-up" label="Profit" value={fmtMoney(totalProfit)} />
              ) : null}
            </View>
          </View>

          {/* Overdue / outstanding across all your customers (all-time running balance) */}
          {data?.overdue && (data.overdue.total > 0 || data.overdue.customer_count > 0) ? (
            <View style={styles.overdueCard} testID="my-report-overdue">
              <View style={styles.overdueIcon}>
                <Ionicons name="alert-circle" size={22} color="#fff" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.overdueLabel}>OVERDUE FROM YOUR CUSTOMERS</Text>
                <Text style={styles.overdueValue}>{fmtMoney(data.overdue.total)}</Text>
                <Text style={styles.overdueSub}>
                  across {data.overdue.customer_count} customer{data.overdue.customer_count === 1 ? "" : "s"} · unpaid sales &amp; invoices
                </Text>
              </View>
            </View>
          ) : null}

          {rows.length === 0 ? (
            <View style={styles.center}>
              <Ionicons name="bar-chart-outline" size={56} color={theme.color.borderStrong} />
              <Text style={styles.emptyTitle}>No data yet</Text>
              <Text style={styles.emptyText}>Your calls and sales will show up here.</Text>
            </View>
          ) : (
            rows.map((r) => {
              const statuses = STATUS_ORDER.filter((s) => (r.breakdown?.[s] || 0) > 0);
              return (
                <View key={r.key} style={styles.card} testID={`report-${period}-${r.key}`}>
                  <View style={styles.cardTop}>
                    <Text style={styles.cardTitle}>{r.label}</Text>
                    <View style={styles.revPill}>
                      <Text style={styles.revPillText}>{fmtMoney(r.revenue)}</Text>
                    </View>
                  </View>

                  <View style={styles.metricRow}>
                    <View style={styles.metricBox}>
                      <Ionicons name="call-outline" size={16} color={theme.color.brand} />
                      <Text style={styles.metricValue}>{r.calls}</Text>
                      <Text style={styles.metricLabel}>calls</Text>
                    </View>
                    <View style={styles.metricBox}>
                      <Ionicons name="cart-outline" size={16} color={theme.color.brand} />
                      <Text style={styles.metricValue}>{r.sales_count}</Text>
                      <Text style={styles.metricLabel}>sales</Text>
                    </View>
                    <View style={styles.metricBox}>
                      <Ionicons name="document-text-outline" size={16} color={theme.color.brand} />
                      <Text style={styles.metricValue}>{r.invoices_count}</Text>
                      <Text style={styles.metricLabel}>invoices</Text>
                    </View>
                  </View>

                  {isAdmin ? (
                    <View style={styles.profitRow}>
                      <Ionicons name="trending-up" size={15} color={theme.color.success} />
                      <Text style={styles.profitLabel}>Profit (sales + invoices)</Text>
                      <Text
                        style={[
                          styles.profitValue,
                          { color: (r.profit || 0) >= 0 ? theme.color.success : theme.color.error },
                        ]}
                      >
                        {fmtMoney(r.profit)}
                      </Text>
                    </View>
                  ) : null}

                  {statuses.length > 0 ? (
                    <View style={styles.breakRow}>
                      {statuses.map((s) => (
                        <View key={s} style={styles.pill}>
                          <View style={[styles.dot, { backgroundColor: STATUS_COLOR[s] || theme.color.muted }]} />
                          <Text style={styles.pillText}>{STATUS_LABEL[s] || s} · {r.breakdown[s]}</Text>
                        </View>
                      ))}
                    </View>
                  ) : (
                    <Text style={styles.noCalls}>No calls logged</Text>
                  )}
                </View>
              );
            })
          )}
        </ScrollView>
      )}
    </View>
  );
}

function SummaryStat({ icon, label, value }: { icon: keyof typeof Ionicons.glyphMap; label: string; value: string }) {
  return (
    <View style={styles.summaryStat}>
      <Ionicons name={icon} size={16} color="#fff" style={{ opacity: 0.85 }} />
      <Text style={styles.summaryValue}>{value}</Text>
      <Text style={styles.summaryStatLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.color.surface },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: theme.space.xl },
  hdr: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingHorizontal: theme.space.md, paddingVertical: theme.space.md,
    backgroundColor: theme.color.surfaceSecondary, borderBottomWidth: 1, borderBottomColor: theme.color.border,
  },
  backIcon: { width: 32, height: 32, alignItems: "center", justifyContent: "center" },
  hdrTitle: { fontSize: theme.font.scale.xl, fontWeight: "800", color: theme.color.onSurface },
  hdrSub: { fontSize: theme.font.scale.sm, color: theme.color.muted, marginTop: 2 },

  toggleWrap: {
    flexDirection: "row", gap: 6, padding: theme.space.md,
    backgroundColor: theme.color.surfaceSecondary, borderBottomWidth: 1, borderBottomColor: theme.color.border,
  },
  toggleBtn: {
    flex: 1, paddingVertical: 10, borderRadius: theme.radius.md, alignItems: "center",
    backgroundColor: theme.color.surfaceTertiary, borderWidth: 1, borderColor: theme.color.border,
  },
  toggleBtnActive: { backgroundColor: theme.color.brand, borderColor: theme.color.brand },
  toggleText: { fontSize: 14, fontWeight: "800", color: theme.color.onSurfaceTertiary },
  toggleTextActive: { color: theme.color.onBrand },

  summaryCard: {
    backgroundColor: theme.color.surfaceInverse, borderRadius: theme.radius.lg,
    padding: theme.space.lg, marginBottom: theme.space.lg,
  },
  summaryLabel: { color: theme.color.borderStrong, fontSize: 11, fontWeight: "700", letterSpacing: 1.5 },
  summaryRow: { flexDirection: "row", flexWrap: "wrap", gap: theme.space.md, rowGap: theme.space.lg, marginTop: theme.space.md },

  overdueCard: {
    flexDirection: "row", alignItems: "center", gap: theme.space.md,
    backgroundColor: "#FDECEA", borderRadius: theme.radius.lg,
    borderWidth: 1, borderColor: theme.color.error + "55",
    padding: theme.space.lg, marginBottom: theme.space.lg,
  },
  overdueIcon: {
    width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center",
    backgroundColor: theme.color.error,
  },
  overdueLabel: { color: theme.color.error, fontSize: 10, fontWeight: "800", letterSpacing: 1 },
  overdueValue: { color: theme.color.error, fontSize: 24, fontWeight: "900", marginTop: 2, letterSpacing: -0.5 },
  overdueSub: { color: theme.color.error, fontSize: 12, fontWeight: "600", marginTop: 2, opacity: 0.85 },
  summaryStat: { minWidth: "26%", flexGrow: 1, alignItems: "flex-start" },
  summaryValue: { color: "#fff", fontSize: 22, fontWeight: "900", marginTop: 6, letterSpacing: -0.5 },
  summaryStatLabel: { color: theme.color.borderStrong, fontSize: 11, fontWeight: "700", marginTop: 2 },

  card: {
    backgroundColor: theme.color.surfaceSecondary, borderRadius: theme.radius.md,
    padding: theme.space.lg, borderWidth: 1, borderColor: theme.color.border, marginBottom: theme.space.sm,
  },
  cardTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  cardTitle: { fontSize: theme.font.scale.lg, fontWeight: "800", color: theme.color.onSurface, flex: 1 },
  revPill: { backgroundColor: theme.color.brandTertiary, paddingHorizontal: theme.space.md, paddingVertical: 4, borderRadius: theme.radius.pill },
  revPillText: { color: theme.color.brand, fontWeight: "800", fontSize: theme.font.scale.sm },

  metricRow: { flexDirection: "row", gap: theme.space.sm, marginTop: theme.space.md },
  metricBox: {
    flex: 1, flexDirection: "row", alignItems: "center", gap: 4,
    backgroundColor: theme.color.surface, borderRadius: theme.radius.sm, borderWidth: 1, borderColor: theme.color.border,
    paddingHorizontal: theme.space.sm, paddingVertical: 10,
  },
  metricValue: { fontSize: 18, fontWeight: "900", color: theme.color.onSurface },
  metricLabel: { fontSize: 11, color: theme.color.muted, fontWeight: "600" },

  profitRow: {
    flexDirection: "row", alignItems: "center", gap: 8, marginTop: theme.space.md,
    paddingTop: theme.space.md, borderTopWidth: 1, borderTopColor: theme.color.border,
  },
  profitLabel: { flex: 1, fontSize: theme.font.scale.sm, color: theme.color.muted, fontWeight: "700" },
  profitValue: { fontSize: 16, fontWeight: "900", letterSpacing: -0.3 },

  breakRow: { flexDirection: "row", flexWrap: "wrap", gap: theme.space.sm, marginTop: theme.space.md },
  pill: { flexDirection: "row", alignItems: "center", gap: 6, backgroundColor: theme.color.surfaceTertiary, paddingHorizontal: theme.space.md, paddingVertical: 6, borderRadius: theme.radius.pill },
  dot: { width: 8, height: 8, borderRadius: 4 },
  pillText: { fontSize: theme.font.scale.sm, color: theme.color.onSurfaceTertiary, fontWeight: "600" },
  noCalls: { fontSize: 12, color: theme.color.muted, marginTop: theme.space.md, fontStyle: "italic" },

  emptyTitle: { marginTop: theme.space.md, fontSize: theme.font.scale.lg, fontWeight: "700", color: theme.color.onSurface },
  emptyText: { marginTop: 6, fontSize: theme.font.scale.base, color: theme.color.muted, textAlign: "center" },
});
