import { useEffect, useState } from "react";
import { AUTH_BYPASS, supabase } from "@/lib/supabase";

export interface AuthUser {
  id: string;
  email: string | null;
}

const DEV_USER: AuthUser = {
  id: "00000000-0000-0000-0000-000000000002",
  email: "dev@orbitaia.local",
};

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(
    AUTH_BYPASS ? DEV_USER : null,
  );
  const [loading, setLoading] = useState(!AUTH_BYPASS);

  useEffect(() => {
    if (AUTH_BYPASS || !supabase) return;

    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(
        session
          ? { id: session.user.id, email: session.user.email ?? null }
          : null,
      );
      setLoading(false);
    });

    const { data: sub } = supabase.auth.onAuthStateChange((_evt, session) => {
      setUser(
        session
          ? { id: session.user.id, email: session.user.email ?? null }
          : null,
      );
    });

    return () => sub.subscription.unsubscribe();
  }, []);

  async function signOut() {
    if (AUTH_BYPASS || !supabase) return;
    await supabase.auth.signOut();
  }

  return { user, loading, signOut, bypassed: AUTH_BYPASS };
}
