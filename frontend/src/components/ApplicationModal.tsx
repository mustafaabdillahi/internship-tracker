import { Trash, X } from "lucide-react";
import type { Application } from "../types/application";
import ApplicationForm from "./ApplicationForm";
import { useEffect, useState } from "react";
import { deleteApplication } from "../api/applications";
import { useQueryClient } from "@tanstack/react-query";

interface ApplicationModalProps {
  isOpen: boolean;
  onClose: () => void;
  application?: Application;
}

function ApplicationModal(
  {
    isOpen,
    onClose,
    application
  }: ApplicationModalProps
) {

  const isEditing = application !== undefined;
  const [isDeleting, setIsDeleting] = useState(false);
  const queryClient = useQueryClient();

  useEffect(() => {
    if(!isOpen) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if(event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if(!isOpen) {
      return null;
  }

  async function onDelete(application: Application) {
    if(isDeleting) {
      return;
    }

    try {
      setIsDeleting(true);
      await deleteApplication(application.id);

      await queryClient.invalidateQueries({
        queryKey: ["applications"]
      });

      onClose();
    } catch(error) {
      console.error("Failed to delete applicatioon:", error);
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if(event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="application-modal">
        <div className="modal-header">
          <h2>
            {isEditing
                ? "Edit application"
                : "New application"}
          </h2>

          <button
            type="button"
            onClick={onClose}
            aria-label="close"
          >
            <X />
          </button>
          
          {application && (
            <button
              className="delete-application-button"
              type="button"
              onClick={() => onDelete(application)}
              disabled={isDeleting}
              aria-label="close"
            >
              <Trash className="Trash" />
            </button>
          )}
        </div>
        
        <ApplicationForm
          application={application}
          onClose={onClose}
        />

      </div>
    </div>
  );
}

export default ApplicationModal;