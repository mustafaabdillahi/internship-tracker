import { Link } from "react-router-dom";
import type { Application } from "../../types/application";

interface Props {
    application: Application;
}

function ApplicationHeader({ application }: Props) {
    console.log(application);
    return (
        <header>
            <Link to="/applications">
                ← Back to applications
            </Link>

            <div className="mt-4">
                <h1 className="text-2x1 font-bold">
                    {application.company_name ?? "Unknown company"}
                </h1>

                <p className="text-gray-600">
                    {application.role ?? "Unknown role"}
                </p>
            </div>

            <div className="mt-4">
                <span>{application.stage}</span>
            </div>
        </header>
    );
}


export default ApplicationHeader;