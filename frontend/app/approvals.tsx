import React, { useCallback, useState } from "react";
import {
  View, Text, StyleSheet, Pressable, ActivityIndicator, RefreshControl, Alert, Platform, Linking, FlatList,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter, useFocusEffect } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { theme } from "@/src/lib/theme";
import { api, ApprovalItem } from "@/src/lib/api";
import { useAuth } from "@/src/lib/auth";

const KIND_META: Record<string, { label: string; icon: keyof typeof Ionicons.glyphMap; color: string }> = {
  sale: { label: "Sale", icon: "cash-outline", color: "#0E9F6E" },
  invoice: { label: "Invoice", icon: "document-text-outline", color: "#1C64F2" },
  receipt: { label: "Money receipt", icon: "receipt-outline", color: "#B45309" },
};

function fmt(n: number) {
  return `₹${Math.round(n).toLocaleString("en-IN")}`;
}

export default function ApprovalsScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [items, setItems] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    if (!isAdmin) { setLoading(false); return; }
    setErr("");
    try {
      const res = await api.listApprovals();
      setItems(res.items || []);
    } catch (e: any) {
      setErr(String(e?.message || "Failed to load"));
    } finally { setLoading(false); setRefreshing(false); }
  }, [isAdmin]);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const openPdf = (token?: string | null) => {
    if (!token) return;
    const url = `${(process.env.EXPO_PUBLIC_BACKEND_URL || "")}/api/media/${token}`;
    Linking.openURL(url).catch(() => {});
  };

  const act = async (kind: ApprovalItem["kind"], id: string, action: "approve" | "reject") => {
    setBusyId(id);
    try {
      if (action === "approve") await api.approveEntry(kind, id);
      else await api.rejectEntry(kind, id);
      await load();
    } catch (e: any) {
      setErr(String(e?.message || "Action failed"));
    } finally { setBusyId(null); }
  };

  const confirmReject = (item: ApprovalItem) => {
    const title = `Reject & delete this ${item.kind}?`;
    const msg = `${item.customer_name || "Customer"} · ${fmt(item.amount)} by ${item.display_name || item.user}\nThe entry will be permanently deleted.`;
    if (Platform.OS === "web") {
      if (typeof window !== "undefined" && window.confirm(`${title}\n\n${msg}`)) act(item.kind, item.id, "reject");
      return;
    }
    Alert.alert(title, msg, [
      { text: "Cancel", style: "cancel" },
      { text: "Reject & delete", style: "destructive", onPress: () => act(item.kind, item.id, "reject") },
    ]);
  };

  const renderItem = ({ item }: { item: ApprovalItem }) => {
    const meta = KIND_META[item.kind] || KIND_META.sale;
    const busy = busyId === item.id;
    return (
      <View style={styles.card} testID={`appr-${item.kind}-${item.id}`}>
        <View style={styles.cardHead}>
          <View style={[styles.kindBadge, { backgroundColor: meta.color + "1A" }]}>
            <Ionicons name={meta.icon} size={13} color={meta.color} />
            <Text style={[styles.kindText, { color: meta.color }]}>
              {item.doc_no ? `${meta.label} ${item.doc_no}` : meta.label}
            </Text>
          </View>
          <Text style={styles.amount}>{fmt(item.amount)}</Text>
        </View>
        <Text style={styles.customer} numberOfLines={1}>{item.customer_name || "Customer"}</Text>
        <Text style={styles.meta}>
          by {item.display_name || item.user} · {item.date_key} · {item.payment_mode.toUpperCase()}
        </Text>
        {item.notes ? <Text style={styles.notes} numberOfLines={2}>{item.notes}</Text> : null}
        <View style={styles.actions}>
          {item.pdf_token ? (
            <Pressable style={styles.pdfBtn} onPress={() => openPdf(item.pdf_token)} hitSlop={6}>
              <Ionicons name="document-outline" size={13} color={theme.color.brand} />
              <Text style={styles.pdfText}>PDF</Text>
            </Pressable>
          ) : <View />}
          <View style={styles.actionRight}>
            <Pressable
              style={[styles.actionBtn, styles.rejectBtn]}
              onPress={() => confirmReject(item)}
              disabled={busy}
              testID={`appr-reject-${item.id}`}
            >
              {busy ? <ActivityIndicator size="small" color={theme.color.error} /> : (
                <>
                  <Ionicons name="close-circle-outline" size={15} color={theme.color.error} />
                  <Text style={[styles.actionText, { color: theme.color.error }]}>Reject</Text>
                </>
              )}
            </Pressable>
            <Pressable
              style={[styles.actionBtn, styles.approveBtn]}
              onPress={() => act(item.kind, item.id, "approve")}
              disabled={busy}
              testID={`appr-approve-${item.id}`}
            >
              {busy ? <ActivityIndicator size="small" color="#fff" /> : (
                <>
                  <Ionicons name="checkmark-circle-outline" size={15} color="#fff" />
                  <Text style={[styles.actionText, { color: "#fff" }]}>Approve</Text>
                </>
              )}
            </Pressable>
          </View>
        </View>
      </View>
    );
  };

  if (!isAdmin) {
    return (
      <View style={[styles.container, { paddingTop: insets.top, alignItems: "center", justifyContent: "center", padding: 24 }]}>
        <Ionicons name="lock-closed-outline" size={32} color={theme.color.muted} />
        <Text style={styles.emptyText}>Only the admin can review pending entries.</Text>
        <Pressable onPress={() => router.back()} style={styles.backBtn}><Text style={styles.backBtnText}>Go back</Text></Pressable>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.iconBtn} testID="appr-back" hitSlop={8}>
          <Ionicons name="arrow-back" size={22} color={theme.color.onSurface} />
        </Pressable>
        <Text style={styles.headerTitle}>Pending approvals</Text>
        <View style={{ width: 36 }} />
      </View>
      <Text style={styles.sub}>
        Employee entries count in reports right away — approving just clears the review flag. Rejecting deletes the entry.
      </Text>
      {err ? <Text style={styles.err}>{err}</Text> : null}
      {loading ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <ActivityIndicator size="large" color={theme.color.brand} />
        </View>
      ) : (
        <FlatList
          data={items}
          renderItem={renderItem}
          keyExtractor={(i) => `${i.kind}-${i.id}`}
          contentContainerStyle={{ padding: theme.space.md, paddingBottom: insets.bottom + 24 }}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={theme.color.brand} />}
          ListEmptyComponent={
            <View style={{ alignItems: "center", marginTop: 80, gap: 8 }}>
              <Ionicons name="checkmark-done-circle-outline" size={40} color={theme.color.success} />
              <Text style={styles.emptyText}>All caught up — nothing pending review.</Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.color.surface },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: theme.space.md, paddingVertical: theme.space.sm },
  iconBtn: { width: 36, height: 36, borderRadius: 18, alignItems: "center", justifyContent: "center" },
  headerTitle: { fontSize: 17, fontWeight: "800", color: theme.color.onSurface },
  sub: { fontSize: 11, color: theme.color.muted, paddingHorizontal: theme.space.md, marginBottom: 4, lineHeight: 15 },
  err: { color: theme.color.error, fontSize: 12, textAlign: "center", marginVertical: 6 },
  card: {
    backgroundColor: theme.color.surfaceSecondary, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.color.border,
    padding: theme.space.md, marginBottom: theme.space.sm,
  },
  cardHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 6 },
  kindBadge: { flexDirection: "row", alignItems: "center", gap: 5, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  kindText: { fontSize: 11, fontWeight: "700" },
  amount: { fontSize: 16, fontWeight: "800", color: theme.color.onSurface },
  customer: { fontSize: 14, fontWeight: "700", color: theme.color.onSurface },
  meta: { fontSize: 11, color: theme.color.muted, marginTop: 2 },
  notes: { fontSize: 11, color: theme.color.onSurfaceTertiary, marginTop: 4, fontStyle: "italic" },
  actions: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 10 },
  actionRight: { flexDirection: "row", gap: 8 },
  actionBtn: { flexDirection: "row", alignItems: "center", gap: 5, height: 34, paddingHorizontal: 14, borderRadius: 17 },
  approveBtn: { backgroundColor: theme.color.success },
  rejectBtn: { backgroundColor: "#FDE8E6" },
  actionText: { fontSize: 12, fontWeight: "800" },
  pdfBtn: { flexDirection: "row", alignItems: "center", gap: 4, height: 34, paddingHorizontal: 10 },
  pdfText: { fontSize: 12, fontWeight: "700", color: theme.color.brand },
  emptyText: { fontSize: 13, color: theme.color.muted, textAlign: "center", marginTop: 8 },
  backBtn: { marginTop: 16, height: 40, paddingHorizontal: 20, borderRadius: 20, backgroundColor: theme.color.brand, alignItems: "center", justifyContent: "center" },
  backBtnText: { color: "#fff", fontWeight: "700", fontSize: 13 },
});
