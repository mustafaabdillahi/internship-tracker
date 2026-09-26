import { useDraggable } from "@dnd-kit/core";
import type { Application } from "../types/application";

interface ApplicationCardProps {
  application: Application;
  isOverlay?: boolean;
  isDragging?: boolean;
}

function ApplicationCard(
  {
      application,
      isOverlay = false,
      isDragging = false
  }: ApplicationCardProps
) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform
  } = useDraggable({
    id: application.id,
    disabled: isOverlay
  });

  const style = !isOverlay && transform
    ? {
      transform:
        `translate3d(${transform.x}px), ${transform.y}px, 0`
    }
    : undefined;

  return (
    <div
      ref={isOverlay ? undefined : setNodeRef}
      style={{
        opacity: isDragging ? 0 : 1
      }}
      {...(!isOverlay ? listeners: {})}
      {...(!isOverlay ? attributes: {})}
      className={`application-card ${
        isOverlay ? "application-card-overlay": ""
      }`}
    >
      <strong>
        {application.company_name ?? "Unknown company"}
        
      </strong>
      <p>
        Role: {application.role ?? "Unknown"}
      </p>

      {application.loc && (
        <p>{application.loc}</p>
      )}
    </div>
  );
}

export default ApplicationCard;