import {
  View,
  Text,
  StyleSheet,
  Pressable,
  FlatList,
  ActivityIndicator,
  RefreshControl,
  Modal,
  TextInput,
  Platform,
  KeyboardAvoidingView,
} from "react-native";
import { useCallback, useState } from "react";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { useRouter, useFocusEffect } from "expo-router";

import { theme } from "@/src/lib/theme";
import { api, Delivery } from "@/src/lib/api";
import { fmtDMY } from "@/src/lib/date";

const fmt = (n: number) => "₹" + (Math.round(n * 100) / 100).toLocaleString("en-IN");
const prettyDate = (iso?: string | null) => fmtDMY(iso);
const daysFromToday = (iso?: string | null) => {
  if (!iso) return null;
  const d = new Date((iso.length === 10 ? iso + "T00:00:00" : iso));
  if (isNaN(d.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diff = Math.round((d.getTime() - today.getTime()) / 86400000);
  return diff;
};

type TabKey = "pending" | "delivered";

export default function DeliveriesScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [tab, setTab] = useState<TabKey>("pending");
  const [rows, setRows] = useState<Delivery[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [overdueCount, setOverdueCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [toast, setToast] = useState("");
  const [markTarget, setMarkTarget] = useState<Delivery | null>(null);
  const [markNote, setMarkNote] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (t: TabKey) => {
    try {
      const r = await api.listDeliveries(t);
      setRows(r.deliveries);
      setPendingCount(r.pending_count);
      setOverdueCount(r.overdue_count);
    } catch {
      setRows([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      load(tab);
    }, [tab, load]),
  );

  const onRefresh = () => {
    setRefreshing(true);
    load(tab);
  };

  const openMark = (d: Delivery) => {
    setMarkTarget(d);
    setMarkNote("");
  };

  const confirmDelivered = async () => {
    if (!markTarget) return;
    setBusy(true);
    try {
      await api.updateDelivery(markTarget.id, { mark_delivered: true, delivery_note: markNote.trim() || undefined });
      setMarkTarget(null);
      setToast(`Marked delivered · ${markTarget.receipt_no}`);
      setTimeout(() => setToast(""), 2200);
      await load(tab);
    } catch (e: any) {
      setToast(String(e?.message || "Failed"));
      setTimeout(() => setToast(""), 2600);
    } finally {
      setBusy(false);
    }
  };

  const reopen = async (d: Delivery) => {
    setBusy(true);
    try {
      await api.updateDelivery(d.id, { reopen: true });
      await load(tab);
    } catch {
    } finally {
      setBusy(false);
    }
  };

  const renderItem = ({ item }: { item: Delivery }) => {
    const isPending = item.delivery_status === "pending";
    const diff = daysFromToday(item.delivery_due_date);
    let dueBadge = "";
    let dueColor = theme.color.muted;
    if (isPending) {
      if (item.overdue) {
        dueBadge = diff === -1 ? "Overdue by 1 day" : `Overdue by ${Math.abs(diff || 0)} days`;
        dueColor = theme.color.error;
      } else if (diff === 0) {
        dueBadge = "Due today";
        dueColor = "#B45309";
      } else if (diff === 1) {
        dueBadge = "Due tomorrow";
        dueColor = "#B45309";
      } else if (diff != null) {
        dueBadge = `Due in ${diff} days`;
        dueColor = theme.color.success;
      }
    }
    return (
      <View style={[styles.card, isPending && item.overdue && styles.cardOverdue]}>
        <View style={styles.cardTop}>
          <View style={{ flex: 1 }}>
            <Text style={styles.custName}>{item.customer_name}</Text>
            <Text style={styles.metaLine}>
              {item.customer_mobile || "—"} · {item.receipt_no}
            </Text>
          </View>
          <Text style={styles.amt}>{fmt(item.amount)}</Text>
        </View>

        <View style={styles.rowChips}>
          {isPending ? (
            <View style={[styles.dueChip, { backgroundColor: dueColor + "22", borderColor: dueColor }]}>
              <Ionicons
                name={item.overdue ? "alert-circle" : "time-outline"}
                size={12}
                color={dueColor}
              />
              <Text style={[styles.dueChipText, { color: dueColor }]}>
                {dueBadge} · {prettyDate(item.delivery_due_date)}
              </Text>
            </View>
          ) : (
            <View style={[styles.dueChip, { backgroundColor: theme.color.success + "22", borderColor: theme.color.success }]}>
              <Ionicons name="checkmark-circle" size={12} color={theme.color.success} />
              <Text style={[styles.dueChipText, { color: theme.color.success }]}>
                Delivered {prettyDate(item.delivered_at)}
              </Text>
            </View>
          )}
        </View>

        {item.narration ? <Text style={styles.narration}>Note: {item.narration}</Text> : null}
        {item.delivery_note ? <Text style={styles.narration}>Delivery: {item.delivery_note}</Text> : null}
        <Text style={styles.byLine}>By {item.display_name || item.user}</Text>

        <View style={styles.actions}>
          {isPending ? (
            <Pressable style={styles.deliverBtn} onPress={() => openMark(item)} testID={`deliver-${item.id}`}>
              <Ionicons name="checkmark-done-outline" size={16} color="#fff" />
              <Text style={styles.deliverBtnText}>Mark delivered</Text>
            </Pressable>
          ) : (
            <Pressable style={styles.reopenBtn} onPress={() => reopen(item)} testID={`reopen-${item.id}`}>
              <Ionicons name="refresh-outline" size={15} color={theme.color.brand} />
              <Text style={styles.reopenBtnText}>Reopen</Text>
            </Pressable>
          )}
        </View>
      </View>
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]} testID="deliveries-screen">
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} hitSlop={10} style={styles.backBtn} testID="deliveries-back">
          <Ionicons name="chevron-back" size={24} color={theme.color.onSurface} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={styles.headerTitle}>Pending Deliveries</Text>
          <Text style={styles.headerSubtitle}>
            {pendingCount} awaiting{overdueCount > 0 ? ` · ${overdueCount} overdue` : ""}
          </Text>
        </View>
      </View>

      <View style={styles.segment}>
        {(["pending", "delivered"] as TabKey[]).map((t) => (
          <Pressable
            key={t}
            onPress={() => setTab(t)}
            style={[styles.segBtn, tab === t && styles.segBtnActive]}
            testID={`deliveries-tab-${t}`}
          >
            <Text style={[styles.segText, tab === t && styles.segTextActive]}>
              {t === "pending" ? "Awaiting" : "Delivered"}
            </Text>
          </Pressable>
        ))}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={theme.color.brand} />
        </View>
      ) : (
        <FlatList
          data={rows}
          keyExtractor={(d) => d.id}
          renderItem={renderItem}
          contentContainerStyle={{ padding: theme.space.lg, paddingBottom: 80 }}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.color.brand} />}
          ListEmptyComponent={
            <View style={styles.empty}>
              <Ionicons name="cube-outline" size={44} color={theme.color.muted} />
              <Text style={styles.emptyTitle}>
                {tab === "pending" ? "No deliveries pending" : "No deliveries yet"}
              </Text>
              <Text style={styles.emptyText}>
                {tab === "pending"
                  ? "When you take an advance and tick “Product to be delivered later” on a money receipt, it shows up here."
                  : "Delivered orders will appear here."}
              </Text>
            </View>
          }
        />
      )}

      {toast ? (
        <View style={[styles.toast, { bottom: insets.bottom + 20 }]}>
          <Text style={styles.toastText}>{toast}</Text>
        </View>
      ) : null}

      <Modal visible={!!markTarget} transparent animationType="fade" onRequestClose={() => setMarkTarget(null)}>
        <KeyboardAvoidingView
          behavior={Platform.OS === "ios" ? "padding" : undefined}
          style={styles.modalOverlay}
        >
          <Pressable style={StyleSheet.absoluteFill} onPress={() => setMarkTarget(null)} />
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Mark delivered</Text>
            <Text style={styles.modalSub}>
              {markTarget?.customer_name} · {fmt(markTarget?.amount || 0)}
            </Text>
            <Text style={styles.label}>Delivery note (optional)</Text>
            <TextInput
              value={markNote}
              onChangeText={setMarkNote}
              placeholder="e.g. Handed over to customer, signed"
              placeholderTextColor={theme.color.muted}
              multiline
              style={styles.noteInput}
              testID="deliver-note"
            />
            <View style={styles.modalActions}>
              <Pressable style={styles.cancelBtn} onPress={() => setMarkTarget(null)} disabled={busy}>
                <Text style={styles.cancelBtnText}>Cancel</Text>
              </Pressable>
              <Pressable style={[styles.confirmBtn, busy && { opacity: 0.6 }]} onPress={confirmDelivered} disabled={busy} testID="deliver-confirm">
                {busy ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.confirmBtnText}>Confirm delivered</Text>
                )}
              </Pressable>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.color.surface },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: theme.space.md,
    paddingVertical: theme.space.md,
    backgroundColor: theme.color.surfaceSecondary,
    borderBottomWidth: 1,
    borderBottomColor: theme.color.border,
    gap: 6,
  },
  backBtn: { padding: 2 },
  headerTitle: { fontSize: theme.font.scale.xxl, fontWeight: "800", color: theme.color.onSurface },
  headerSubtitle: { fontSize: theme.font.scale.sm, color: theme.color.muted, marginTop: 2 },
  segment: {
    flexDirection: "row",
    margin: theme.space.lg,
    marginBottom: 0,
    backgroundColor: theme.color.surfaceTertiary,
    borderRadius: theme.radius.md,
    padding: 4,
    gap: 4,
  },
  segBtn: { flex: 1, paddingVertical: 9, borderRadius: theme.radius.sm, alignItems: "center" },
  segBtnActive: { backgroundColor: theme.color.brand },
  segText: { fontSize: theme.font.scale.md, fontWeight: "700", color: theme.color.muted },
  segTextActive: { color: "#fff" },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  card: {
    backgroundColor: theme.color.surfaceSecondary,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.color.border,
    padding: theme.space.md,
    marginBottom: theme.space.md,
  },
  cardOverdue: { borderColor: theme.color.error, backgroundColor: "#FEF2F2" },
  cardTop: { flexDirection: "row", alignItems: "flex-start" },
  custName: { fontSize: theme.font.scale.lg, fontWeight: "800", color: theme.color.onSurface },
  metaLine: { fontSize: theme.font.scale.sm, color: theme.color.muted, marginTop: 2 },
  amt: { fontSize: theme.font.scale.xl, fontWeight: "800", color: theme.color.brand },
  rowChips: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 10 },
  dueChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
    borderWidth: 1,
  },
  dueChipText: { fontSize: 11, fontWeight: "700" },
  narration: { fontSize: theme.font.scale.sm, color: theme.color.onSurface, marginTop: 8 },
  byLine: { fontSize: 11, color: theme.color.muted, marginTop: 6 },
  actions: { flexDirection: "row", justifyContent: "flex-end", marginTop: 10 },
  deliverBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: theme.color.brand,
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: theme.radius.md,
  },
  deliverBtnText: { color: "#fff", fontWeight: "700", fontSize: theme.font.scale.md },
  reopenBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    borderWidth: 1,
    borderColor: theme.color.brand,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: theme.radius.md,
  },
  reopenBtnText: { color: theme.color.brand, fontWeight: "700", fontSize: theme.font.scale.md },
  empty: { alignItems: "center", paddingTop: 80, paddingHorizontal: 32, gap: 8 },
  emptyTitle: { fontSize: theme.font.scale.lg, fontWeight: "800", color: theme.color.onSurface, marginTop: 6 },
  emptyText: { fontSize: theme.font.scale.sm, color: theme.color.muted, textAlign: "center", lineHeight: 19 },
  toast: {
    position: "absolute",
    alignSelf: "center",
    backgroundColor: theme.color.onSurface,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 999,
  },
  toastText: { color: theme.color.surface, fontWeight: "600", fontSize: theme.font.scale.sm },
  modalOverlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "center", padding: theme.space.lg },
  modalCard: { backgroundColor: theme.color.surface, borderRadius: theme.radius.lg, padding: theme.space.lg },
  modalTitle: { fontSize: theme.font.scale.xl, fontWeight: "800", color: theme.color.onSurface },
  modalSub: { fontSize: theme.font.scale.sm, color: theme.color.muted, marginTop: 2, marginBottom: theme.space.md },
  label: {
    fontSize: 12,
    fontWeight: "700",
    color: theme.color.muted,
    letterSpacing: 0.5,
    textTransform: "uppercase",
    marginBottom: 6,
  },
  noteInput: {
    borderWidth: 1,
    borderColor: theme.color.border,
    backgroundColor: theme.color.surfaceSecondary,
    borderRadius: theme.radius.md,
    padding: theme.space.md,
    minHeight: 64,
    textAlignVertical: "top",
    color: theme.color.onSurface,
    fontSize: 15,
  },
  modalActions: { flexDirection: "row", gap: 10, marginTop: theme.space.lg },
  cancelBtn: { flex: 1, paddingVertical: 13, borderRadius: theme.radius.md, alignItems: "center", borderWidth: 1, borderColor: theme.color.border },
  cancelBtnText: { fontWeight: "700", color: theme.color.muted, fontSize: theme.font.scale.md },
  confirmBtn: { flex: 2, paddingVertical: 13, borderRadius: theme.radius.md, alignItems: "center", backgroundColor: theme.color.brand },
  confirmBtnText: { fontWeight: "800", color: "#fff", fontSize: theme.font.scale.md },
});
