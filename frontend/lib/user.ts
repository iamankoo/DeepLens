import type { UserPublic } from "@/types/auth";

// New registrations always have a name; existing accounts predating that
// requirement don't, so every display site falls back to the email's
// local part rather than assuming `name` is set.
export function displayName(user: Pick<UserPublic, "name" | "email">): string {
  return user.name?.trim() || user.email.split("@")[0];
}

export function initialsFor(user: Pick<UserPublic, "name" | "email">): string {
  return displayName(user).slice(0, 2).toUpperCase();
}
