import { ReactNode } from "react";
import { ChatShell } from "@/widgets/chat-shell/ui/chat-shell";

interface ChatLayoutProps {
  children: ReactNode;
}

export default function ChatLayout({ children }: ChatLayoutProps) {
  return <ChatShell>{children}</ChatShell>;
}
