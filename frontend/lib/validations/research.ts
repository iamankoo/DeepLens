import * as z from "zod";

export const newResearchSchema = z.object({
  query: z
    .string()
    .min(10, "Describe what you'd like researched in a bit more detail (10+ characters)")
    .max(2000, "Keep the query under 2000 characters"),
});
export type NewResearchFormValues = z.infer<typeof newResearchSchema>;
