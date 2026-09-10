import { Stack, useRouter, useSegments } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { useEffect } from "react";
import { LogBox, Platform, View, Text, StyleSheet, ActivityIndicator } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { KeyboardProvider } from "react-native-keyboard-controller";
import * as Notifications from "expo-notifications";
import * as Linking from "expo-linking";

import { Ionicons } from "@expo/vector-icons";

import { useIconFonts } from "@/src/hooks/use-icon-fonts";
import { registerForPush } from "@/src/lib/push";
import { AuthProvider, useAuth } from "@/src/lib/auth";
import { storage } from "@/src/utils/storage";
import { theme } from "@/src/lib/theme";

LogBox.ignoreAllLogs(true);
SplashScreen.preventAutoHideAsync();

if (Platform.OS !== "web") {
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: true,
      shouldSetBadge: false,
    }),
  });
}

if (Platform.OS === "android") {
  Notifications.setNotificationChannelAsync("default", {
    name: "Default",
    importance: Notifications.AndroidImportance.MAX,
    sound: "default",
  });
}

function Gate() {
  const { user, loading } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    const first = segments[0] as string | undefined;
    const inAuthGroup = first === "login";
    // `first === undefined` means we're on the bare index route (app/index.tsx),
    // which is just a splash/logo with no navigation of its own.
    const atSplash = first === undefined;
    if (!user && !inAuthGroup) {
      router.replace("/login");
    } else if (user && (inAuthGroup || atSplash)) {
      // Already signed in but sitting on the login or splash screen (e.g. on a
      // cold app relaunch) — move to the dashboard so we never dead-end on the logo.
      router.replace("/(tabs)");
    }
  }, [user, loading, segments, router]);

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: theme.color.surface }}>
        <ActivityIndicator color={theme.color.brand} />
      </View>
    );
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="login" />
      <Stack.Screen name="(tabs)" />
      <Stack.Screen name="settings" options={{ presentation: "card" }} />
      <Stack.Screen name="admin" options={{ presentation: "card" }} />
      <Stack.Screen name="history" options={{ presentation: "card" }} />
      <Stack.Screen name="my-report" options={{ presentation: "card" }} />
      <Stack.Screen name="deliveries" options={{ presentation: "card" }} />
      <Stack.Screen name="attendance" options={{ presentation: "card" }} />
      <Stack.Screen name="sales" options={{ presentation: "card" }} />
      <Stack.Screen name="expenses" options={{ presentation: "card" }} />
      <Stack.Screen name="reports" options={{ presentation: "card" }} />
      <Stack.Screen name="feedback/[id]" options={{ presentation: "modal" }} />
    </Stack>
  );
}

function WebBlocked() {
  return (
    <View style={wb.container}>
      <View style={wb.card}>
        <View style={wb.iconWrap}>
          <Ionicons name="phone-portrait-outline" size={40} color={theme.color.brand} />
        </View>
        <Text style={wb.title}>Available on mobile only</Text>
        <Text style={wb.sub}>
          Pritha Cabinet now runs exclusively on the mobile app for a faster, more secure experience.
        </Text>
        <View style={wb.stepsBox}>
          <View style={wb.stepRow}>
            <Ionicons name="download-outline" size={18} color={theme.color.brand} />
            <Text style={wb.stepText}>Install the app on your Android or iOS phone.</Text>
          </View>
          <View style={wb.stepRow}>
            <Ionicons name="log-in-outline" size={18} color={theme.color.brand} />
            <Text style={wb.stepText}>Open it and sign in with your usual credentials.</Text>
          </View>
        </View>
        <Text style={wb.footer}>The web version has been discontinued.</Text>
      </View>
    </View>
  );
}

export default function RootLayout() {
  const [loaded, error] = useIconFonts();
  const router = useRouter();

  useEffect(() => {
    if (loaded || error) SplashScreen.hideAsync();
  }, [loaded, error]);

  useEffect(() => {
    if (Platform.OS === "web") return;

    registerForPush().catch(() => {});

    const tapSub = Notifications.addNotificationResponseReceivedListener((response) => {
      const data = (response.notification.request.content.data || {}) as any;
      const url = data.deeplink || data.action_url;
      if (!url) return;
      url.startsWith("http") ? Linking.openURL(url) : router.push(url);
    });

    Notifications.getLastNotificationResponseAsync().then((response) => {
      if (!response) return;
      const data = (response.notification.request.content.data || {}) as any;
      const url = data.deeplink || data.action_url;
      if (url) url.startsWith("http") ? Linking.openURL(url) : router.push(url);
    });

    (async () => {
      try {
        const { status, canAskAgain } = await Notifications.getPermissionsAsync();
        if (status !== "denied" || canAskAgain) return;
        const lastNudge = await storage.getItem("pushNudgeAt", "");
        const oneWeek = 7 * 24 * 60 * 60 * 1000;
        if (lastNudge && Date.now() - Number(lastNudge) <= oneWeek) return;
        await storage.setItem("pushNudgeAt", String(Date.now()));
        Linking.openSettings();
      } catch {}
    })();

    return () => {
      tapSub.remove();
    };
  }, [router]);

  if (!loaded && !error) return null;

  // Web version discontinued for PRODUCTION only — the dev/preview browser still
  // works so the app can be previewed here. Published/hosted web builds are blocked.
  if (Platform.OS === "web" && !__DEV__) {
    return (
      <SafeAreaProvider>
        <WebBlocked />
      </SafeAreaProvider>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: theme.color.surfaceTertiary }}>
      <KeyboardProvider>
        <SafeAreaProvider>
          <AuthProvider>
            {/* On a computer browser keep the app in a centered, readable column (admin & collector use the web). */}
            <View style={Platform.OS === "web" ? webShell : { flex: 1 }}>
              <Gate />
            </View>
          </AuthProvider>
        </SafeAreaProvider>
      </KeyboardProvider>
    </GestureHandlerRootView>
  );
}

const webShell = {
  flex: 1,
  width: "100%" as const,
  maxWidth: 1180,
  alignSelf: "center" as const,
  backgroundColor: theme.color.surface,
  // subtle side borders so the column reads as the app on very wide monitors
  borderLeftWidth: 1,
  borderRightWidth: 1,
  borderColor: theme.color.border,
};

const wb = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.color.surfaceTertiary,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  card: {
    width: "100%",
    maxWidth: 420,
    backgroundColor: theme.color.surface,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: theme.color.border,
    padding: 28,
    alignItems: "center",
  },
  iconWrap: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: theme.color.brandTertiary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 18,
  },
  title: { fontSize: 22, fontWeight: "800", color: theme.color.onSurface, textAlign: "center" },
  sub: { fontSize: 14, color: theme.color.muted, textAlign: "center", marginTop: 10, lineHeight: 20 },
  stepsBox: { alignSelf: "stretch", marginTop: 20, gap: 12 },
  stepRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  stepText: { flex: 1, fontSize: 13, color: theme.color.onSurface, fontWeight: "600", lineHeight: 18 },
  footer: { fontSize: 11, color: theme.color.muted, marginTop: 22, fontStyle: "italic" },
});
