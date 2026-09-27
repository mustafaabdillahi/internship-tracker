import { X } from "lucide-react";
import type { Application } from "../types/application";
import ApplicationForm from "./ApplicationForm";
import { useEffect } from "react";

interface ApplicationModalProps {
  isOpen: boolean;
  onClose: () => void;
  application?: Application;
}

function ApplicationModal(
  {
    isOpen,
    onClose,
    application=undefined
  }: ApplicationModalProps
) {

  const isEditing = application !== undefined;

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