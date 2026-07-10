import { relationshipReportStatus } from "../generated/relationshipStatus.generated";

export function RelationshipStatusBadge({ status }: { status: string }) {
  const value = relationshipReportStatus(status);
  return <span className={`relationshipStatus relationshipStatus--${value.tone}`}>{value.label}</span>;
}
