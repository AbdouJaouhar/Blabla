export type Role = "user" | "assistant";

export interface Message {
    id: string;
    role: Role;
    content: string;
    streaming: boolean;
}

export interface PendingImage {
  id: string;
  url: string;
}
