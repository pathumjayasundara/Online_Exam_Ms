/* ExamPortal — shared configuration.
   Change these if either Flask backend runs on another host/port.

   CORE_API     -> backend/core-api      (Admin + Student modules, port 5000)
   LECTURER_API -> backend/lecturer-api  (Lecturer module, port 5001) */
window.EXAMPORTAL_CONFIG = {
  CORE_API: "http://127.0.0.1:5000",
  LECTURER_API: "http://127.0.0.1:5001"
};
