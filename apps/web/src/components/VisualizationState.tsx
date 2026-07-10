import {
  visualizationState,
  type VisualizationState as VisualizationStateName,
} from "../generated/relationshipStatus.generated";

export function VisualizationState({ state, message }: { state: VisualizationStateName; message?: string }) {
  const value = visualizationState(state);
  return (
    <div className={`visualizationState visualizationState--${value.tone}`} role="status">
      <strong>{value.label}</strong>
      <span>{message || value.description}</span>
    </div>
  );
}
