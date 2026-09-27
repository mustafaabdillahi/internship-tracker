import { useDroppable } from "@dnd-kit/core";
import type { Application, ApplicationStage } from "../types/application";
import ApplicationCard from "./ApplicationCard";

interface KanbanColumnProps {
  id: ApplicationStage;
  title: string;
  applications: Application[],
  activeApplicationId: number | null;
  onEdit: (application: Application) => void;
}

function KanbanColumn(
  {
    id,
    title,
    applications,
    activeApplicationId,
    onEdit
}: KanbanColumnProps) {
  const {
    setNodeRef,
    isOver
  } = useDroppable({
    id
  });

  return (
    <div
      ref={setNodeRef}
      className={`kanban-column ${
        isOver ? "kanban-column-over": ""
      }`}
    >
      <h2 className="kanban-column-title">
        {title}
        <span className="kanban-column-count">
          ({applications.length})
        </span>
      </h2>

      <div className="kanban-column-cards">
        {applications.map((application) => (
          <ApplicationCard
            key={application.id}
            application={application}
            isDragging={application.id === activeApplicationId}
            onEdit={onEdit}
          />
        ))}
      </div>

    </div>
  )
}

export default KanbanColumn;