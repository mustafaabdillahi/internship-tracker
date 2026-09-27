import { useState } from "react";
import { type ApplicationFormData, type Application, applicationStages } from "../types/application";
import { createApplication, updateApplication } from "../api/applications";
import { useQueryClient } from "@tanstack/react-query";

interface ApplicationFormProps {
  application?: Application;
  onClose: () => void;
}



function ApplicationForm(
  { application, onClose }: ApplicationFormProps
) {
  const [formData, setFormData] = useState<ApplicationFormData>(() => ({
    company_name: application?.company_name ?? "",
    stage: application?.stage ?? "applied",
    role: application?.role ?? null,
    loc: application?.loc ?? null,
    employment_type: application?.employment_type ?? null,
    notes: application?.notes ?? null
  }));

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();


  function handleChange(
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
) {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value
    }));
  }


  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSubmitting(true);

    try {
      if(application) {
        await updateApplication(application.id, formData);  
      } else {
        await createApplication(formData);
      }

      await queryClient.invalidateQueries({
        queryKey: ["applications"]
      });

      onClose();
    } catch(error) {
      console.error(error);
      setError("Could not save application. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }


  return (
    <form onSubmit={handleSubmit}>
      <div className="form-field">
        <label htmlFor="company_name">Company</label>

        <input
          id="company_name"
          name="company_name"
          value={formData.company_name}
          onChange={handleChange}
          required
        />
      </div>

      <div className="form-field">
        <label htmlFor="role">Role</label>

        <input
          id="role"
          name="role"
          value={formData.role ?? ""}
          onChange={handleChange}
          required
        />
      </div>

      <div className="form-field">
        <label htmlFor="loc">Location</label>

        <input
          id="loc"
          name="loc"
          value={formData.loc ?? ""}
          onChange={handleChange}
        />
      </div>

      <select
        id="stage"
        name="stage"
        value={formData.stage}
        onChange={handleChange}
      >
        {applicationStages.map((stage) => (
          <option key={stage} value={stage}>
            {
              stage === "oa"
                ? "OA"
                : stage.charAt(0).toUpperCase() + stage.slice(1)
            }
          </option>
        ))}
      </select>

      <button type="submit" disabled={isSubmitting}>
        {
          isSubmitting
          ? "Saving..."
          : (application ? "Update" : "Create") 
        }
      </button>

      {error && (
        <div className="form-error">
          {error}
        </div>
      )}
        
    </form>
  );
}

export default ApplicationForm;