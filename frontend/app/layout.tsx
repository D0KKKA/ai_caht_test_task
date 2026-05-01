import "./globals.css";
import type { Metadata } from "next";
import { RootProvider } from "@/shared/providers/root-provider";

export const metadata: Metadata = {
  title: "AI Chat",
  description: "Chat with AI powered by OpenRouter",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body className="bg-white dark:bg-gray-950">
        <RootProvider>{children}</RootProvider>
      </body>
    </html>
  );
}
