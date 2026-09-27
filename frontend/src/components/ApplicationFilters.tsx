import {type Filters } from "../types/application";

interface ApplicationFiltersProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

const emptyFilters: Filters = {
  company: "",
  location: "",
  role: "",
  dateFrom: "",
  dateTo: ""
}


export default function ApplicationFilters({ filters, onChange }: ApplicationFiltersProps) {

  const today = new Date();
  const localToday = new Date(
    today.getTime() - today.getTimezoneOffset() * 60000
  ).toISOString().split("T")[0];

  
  function handleDateChange(name: "dateFrom" | "dateTo", value: string) {
    const year = value.slice(0, 4);

    // Reject if future year has been entered
    if(year.length === 4 && year > localToday.slice(0, 4)) {
      return;
    }

    // Reject future dates
    if(value.length === 10 && value > localToday) {
      return;
    }

    onChange({
      ...filters,
      [name]: value
    });
  }


  return (
    <>
      <input
        type="text"
        name="company"
        placeholder="Company"
        value={filters.company}
        onChange={(event) => {
          onChange({
            ...filters,
            company: event.target.value
          });
        }}
      />

      <input
        type="text"
        name="loc"
        placeholder="Location"
        value={filters.location}
        onChange={(event) => {
          onChange({
            ...filters,
            location: event.target.value,
          });
        }}
      />

      <input
        type="text"
        name="role"
        placeholder="Role"
        value={filters.role}
        onChange={(event) => {
          onChange({
            ...filters,
            role: event.target.value,
          });
        }}
      />

      <br />
      <label htmlFor="dateFrom">
        Applied after
      </label>
      <input
        type="date"
        name="dateFrom"
        max={localToday}
        value={filters.dateFrom}
        onChange={(event) => {
          handleDateChange("dateFrom", event.target.value)
        }}
      />

      <br />
      <label htmlFor="dateTo">
        Applied before
      </label>
      <input
        type="date"
        name="dateTo"
        max={localToday}
        value={filters.dateTo}
        onChange={(event) => {
          handleDateChange("dateTo", event.target.value)
        }}
      />
      
      <br />
      <button
        type="button"
        onClick={() => onChange(emptyFilters)}  
      >
        Clear filters
      </button>

    </>
  );
}