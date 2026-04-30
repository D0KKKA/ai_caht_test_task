import "./globals.css";
import { RootProvider } from "@/shared/providers/root-provider";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "AI Chat",
  description: "Chat with AI powered by OpenRouter",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body className="bg-white dark:bg-gray-950">
        <RootProvider>{children}</RootProvider>
      </body>
    </html>
  );
}
