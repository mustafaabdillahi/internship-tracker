import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { type ApplicationDetail } from "../types/applicationDetail";
import { getApplicationDetails } from "../api/applications";
import ApplicationHeader from "../components/application_details/ApplicationHeader";
import StageTimeline from "../components/application_details/StageTimeline";
import DeadlineList from "../components/application_details/DeadlineList";
import ApplicationNotes from "../components/application_details/ApplicationNotes";

function ApplicationDetails() {
  const { id } = useParams<{ id: string }>();

  const [data, setData] = useState<ApplicationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const applicationId = id ? Number(id) : NaN;
  const invalidId = !id || !Number.isInteger(applicationId);


  useEffect(() => {
    if(invalidId) {
      return;
    }

    async function loadApplication() {
      try {
        setLoading(true);
        setError(null);

        const result = await getApplicationDetails(applicationId);
        console.log(result);
        setData(result);
      } catch(err) {
        console.error(err);
        setError("Failed to load application.");
      } finally {
        setLoading(false);
      }
    }

    loadApplication();
  }, [applicationId, invalidId]);

  if(invalidId) {
    return <p>Error: Invalid application ID.</p>;
  }

  if(loading) {
    return <p>Loading...</p>;
  }

  if(error) {
    return <p>Error: {error}</p>;
  }

  if(!data) {
    return <p>Application not found.</p>;
  }

  return (
    <main className="mx-auto max-w-6x1 p-6">
      <ApplicationHeader
        application={data.application}
      />

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <section className="lg:col-span-2">
          <StageTimeline
            events={data.stage_events}
          />
        </section>
        <aside>
          <DeadlineList
            deadlines={data.deadlines}
          />
          <ApplicationNotes
            notes={data.notes}
          />
        </aside>
      </div>
    </main>
  )

}

export default ApplicationDetails;