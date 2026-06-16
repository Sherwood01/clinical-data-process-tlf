import { StackHandler } from "@hexclave/next";
import { AuthWrapper } from "@/components/auth-wrapper";

export default function HandlerPage() {
  return (
    <AuthWrapper>
      <StackHandler fullPage={false} />
    </AuthWrapper>
  );
}
