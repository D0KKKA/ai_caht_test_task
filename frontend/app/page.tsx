"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useChats } from "@/entities/chat/api/chat-api";

export default function Home() {
  const router = useRouter();
  const { data: chats, isLoading } = useChats();

  useEffect(() => {
    if (!isLoading) {
      if (chats && chats.length > 0) {
        router.replace(`/chat/${chats[0].id}`);
      } else {
        router.replace("/chat");
      }
    }
  }, [chats, isLoading, router]);

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Loading...</h1>
      </div>
    </div>
  );
}
