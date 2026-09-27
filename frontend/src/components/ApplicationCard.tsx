import { useDraggable } from "@dnd-kit/core";
import type { Application } from "../types/application";
import { Pencil } from "lucide-react";

interface ApplicationCardProps {
  application: Application;
  isOverlay?: boolean;
  isDragging?: boolean;
  onEdit: (application: Application) => void;
}

function ApplicationCard(
  {
      application,
      isOverlay = false,
      isDragging = false,
      onEdit
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
        `translate3d(${transform.x}px, ${transform.y}px, 0)`
    }
    : undefined;

  return (
    <div
      ref={isOverlay ? undefined : setNodeRef}
      style={{
        ...style,
        opacity: isDragging ? 0 : 1
      }}
      {...(!isOverlay ? listeners: {})}
      {...(!isOverlay ? attributes: {})}
      className={`application-card ${
        isOverlay ? "application-card-overlay": ""
      }`}
    >

      <button
        type="button"
        className="edit-button"
        onPointerDown={(event) => {
          event.stopPropagation();
        }}
        onClick={(event) => {
          console.log("Clicked!");
          onEdit(application);
        }}
        aria-label={`Edit ${application.company_name ?? "Unknown Company"} ${application.role ?? ""} application`}
      >
        <Pencil size={16} />
      </button>

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