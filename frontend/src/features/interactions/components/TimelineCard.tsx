import Link from "next/link";

import {
  Card,
  CardContent,
  CardHeader,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { InteractionTypeBadge } from "./InteractionTypeBadge";
import type { InteractionResponse } from "@/features/interactions/types";

interface Props {
  interaction: InteractionResponse;
  showLink?: boolean;
}

export function TimelineCard({ interaction, showLink = true }: Props) {
  const meetingDate = new Date(interaction.meeting_date).toLocaleDateString(
    "en-US",
    { year: "numeric", month: "long", day: "numeric", hour: "2-digit", minute: "2-digit" }
  );
  const createdBy = interaction.created_by_user
    ? `${interaction.created_by_user.first_name} ${interaction.created_by_user.last_name}`
    : null;

  return (
    <Card className="transition-shadow hover:shadow-sm">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            {showLink ? (
              <Link
                href={`/interactions/${interaction.id}`}
                className="font-medium hover:underline line-clamp-1"
              >
                {interaction.title}
              </Link>
            ) : (
              <p className="font-medium line-clamp-1">{interaction.title}</p>
            )}
            <p className="text-xs text-muted-foreground mt-0.5">{meetingDate}</p>
          </div>
          <InteractionTypeBadge type={interaction.interaction_type} />
        </div>
      </CardHeader>

      {interaction.notes && (
        <>
          <Separator />
          <CardContent className="pt-3">
            <p className="text-sm text-muted-foreground line-clamp-3">
              {interaction.notes}
            </p>
            {createdBy && (
              <p className="text-xs text-muted-foreground mt-2">
                Logged by {createdBy}
              </p>
            )}
          </CardContent>
        </>
      )}
    </Card>
  );
}
