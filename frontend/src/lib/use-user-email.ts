"use client";

import { useEffect, useState } from "react";
import { useSessionContext } from "supertokens-auth-react/recipe/session";

/**
 * Hook that returns the current user's email.
 *
 * First tries the access token payload (fast, local).
 * Falls back to fetching /api/v1/users/me when the email
 * hasn't been written into the token yet (first load).
 */
export function useUserEmail(): {
  email: string | null;
  loading: boolean;
} {
  const session = useSessionContext();
  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Extract payload email outside the effect to avoid TS type narrowing issue
  const payloadEmail = !session.loading ? session.accessTokenPayload?.email : undefined;

  useEffect(() => {
    if (session.loading) return;

    if (payloadEmail) {
      setEmail(payloadEmail);
      setLoading(false);
      return;
    }

    fetch("/api/v1/users/me")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.email) setEmail(data.email);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [session.loading, payloadEmail]);

  return { email, loading };
}
