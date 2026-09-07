import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { storage } from "@/src/utils/storage";
import { api, TOKEN_KEY, USER_KEY, User } from "@/src/lib/api";

type AuthCtx = {
  user: User | null;
  token: string | null;
  loading: boolean;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  refresh: () => Promise<void>;
};

const Ctx = createContext<AuthCtx | null>(null);

// Resolve/reject `p`, but give up after `ms` so a slow/stalled network request
// can NEVER block app startup (fixes: APK opens once, then hangs on relaunch).
function withTimeout<T>(p: Promise<T>, ms: number): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("timeout")), ms);
    p.then(
      (v) => {
        clearTimeout(timer);
        resolve(v);
      },
      (e) => {
        clearTimeout(timer);
        reject(e);
      },
    );
  });
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const bootstrap = async () => {
    try {
      const stored = await storage.secureGet(TOKEN_KEY, "");
      if (!stored) {
        setLoading(false);
        return;
      }
      setToken(stored as string);

      // Optimistically restore the last known user so the app opens INSTANTLY
      // (even offline). We never block the first render on a network call.
      const cachedRaw = await storage.getItem(USER_KEY, "");
      if (cachedRaw) {
        try {
          setUser(JSON.parse(cachedRaw as string) as User);
        } catch {}
      }
      setLoading(false);

      // Verify/refresh the session in the background with a hard timeout.
      try {
        const me = await withTimeout(api.me(), 8000);
        setUser(me);
        await storage.setItem(USER_KEY, JSON.stringify(me));
      } catch (e: any) {
        // Only a real auth failure means the session is invalid -> sign out.
        // Network errors / timeouts keep the cached session so the app works offline.
        if (e && (e.status === 401 || e.status === 403)) {
          await storage.secureRemove(TOKEN_KEY);
          await storage.removeItem(USER_KEY);
          setToken(null);
          setUser(null);
        }
      }
    } catch {
      // Never let bootstrap crash/hang the app.
      setLoading(false);
    }
  };

  useEffect(() => {
    bootstrap();
  }, []);

  const signIn = async (username: string, password: string) => {
    const res = await api.login(username, password);
    await storage.secureSet(TOKEN_KEY, res.access_token);
    await storage.setItem(USER_KEY, JSON.stringify(res.user));
    setToken(res.access_token);
    setUser(res.user);
  };

  const signOut = async () => {
    await storage.secureRemove(TOKEN_KEY);
    await storage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  };

  const refresh = async () => {
    try {
      const me = await api.me();
      setUser(me);
      await storage.setItem(USER_KEY, JSON.stringify(me));
    } catch {}
  };

  return (
    <Ctx.Provider value={{ user, token, loading, signIn, signOut, refresh }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth outside AuthProvider");
  return v;
}
