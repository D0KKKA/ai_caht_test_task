const PENDING_MESSAGE_PREFIX = "pending-message:";

export function getPendingMessageStorageKey(chatId: string): string {
  return `${PENDING_MESSAGE_PREFIX}${chatId}`;
}
