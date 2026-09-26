import { DndContext, DragOverlay, type DragEndEvent, type DragStartEvent } from "@dnd-kit/core";
import type { Application, ApplicationStage } from "../types/application";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApplications, updateApplicationStage } from "../api/applications";
import KanbanColumn from "./KanbanColumn";
import { useState } from "react";
import ApplicationCard from "./ApplicationCard";

const columns: {
  id: ApplicationStage;
  title: string;
}[] = [
  {
    id: "applied",
    title: "Applied"
  },
  {
    id: "interview",
    title: "Interview"
  },
  {
    id: "offer",
    title: "Offer"
  },
  {
    id: "rejected",
    title: "Rejected"
  },
  {
    id: "withdrawn",
    title: "Withdrawn"
  }
];



function KanbanBoard() {
  const queryClient = useQueryClient();

  const {
    data: applications = [],
    isPending,
    isError,
    error
  } = useQuery({
    queryKey: ["applications"],
    queryFn: getApplications
  });

  const updateStageMutation = useMutation({
    mutationFn: ({
      id, stage
    }: {
      id: number,
      stage: ApplicationStage;
    }) => updateApplicationStage(id, stage),

    onMutate: async({ id, stage }) => {
      await queryClient.cancelQueries({
        queryKey: ["applications"]
      });

      const previousApplications = queryClient.getQueryData<Application[]>(
        ["applications"]
      );

      queryClient.setQueryData<Application[]>(
        ["applications"],
        (currentApplications = []) =>
            currentApplications.map((application) =>
            application.id === id
            ? {
              ...application,
              stage
            }
            : application
          )
      );

      return { previousApplications };
    },

    onError: (_error, _variables, context) => {
      if(context?.previousApplications) {
        queryClient.setQueryData(
          ["applications"],
          context.previousApplications
        );
      }
    },

    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["applications"]
      });
    }
  });

  const [activeApplicationId, setActiveApplicationId] =
    useState<number | null>(null);
  
  function handleDragStart(event: DragStartEvent) {
    setActiveApplicationId(Number(event.active.id));
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;

    setActiveApplicationId(null);

    if(!over) {
      return;
    }

    const applicationId = Number(active.id);

    const application = applications.find(
      (application) => application.id === applicationId
    );

    if(!application) {
      return;
    }

    const newStage = over.id as ApplicationStage;

    // Don't update anything if the application wasn't moved to another column
    if(application.stage === newStage) {
      return;
    }

    updateStageMutation.mutate({
      id: applicationId,
      stage: newStage
    });

  }

  const activeApplication = applications.find(
    (application) => application.id === activeApplicationId
  );

  if(isPending) {
    return <p>Loading applications...</p>;
  }

  if(isError) {
    return (
      <p>Failed to load applications: {error.message}</p>
    );
  }

  
  return (
    <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="kanban-board">
        {columns.map((column) => {
          const columnApplications = applications.filter(
            (application) => application.stage === column.id
          );

          return (
            <KanbanColumn
              key={column.id}
              id={column.id}
              title={column.title}
              applications={columnApplications}
              activeApplicationId={activeApplicationId}
            />
          );

        })}
      </div>
      <DragOverlay dropAnimation={null}>
        {activeApplication ? (
          <ApplicationCard
            application={activeApplication}
            isOverlay
          />
        ): null}
      </DragOverlay>
    </DndContext>
  );
}

export default KanbanBoard;
