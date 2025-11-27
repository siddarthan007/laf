# FINDORA: AI-Powered Lost & Found Portal

**Overview:**
FINDORA is a modern, AI-powered lost and found portal designed to streamline the recovery of lost items within university campuses and large institutions. By leveraging advanced vector similarity search and transformer embeddings, FINDORA automates the matching process between lost and found reports, significantly reducing the manual effort required by administrators and increasing the recovery rate for students and staff. The platform ensures a secure, efficient, and transparent process for reporting, matching, and claiming items.

**Key Features:**

1.  **User Onboarding & Verification:**
    *   **Secure Registration:** Students and staff register with institutional details (Roll Number, Email, Hostel).
    *   **Authentication:** Robust JWT-based authentication with access and refresh token rotation.
    *   **Role-Based Access:** Distinct roles for standard Users and Administrators.

2.  **Student/Staff Capabilities:**
    *   **Report Lost Items:** Submit detailed reports for lost items including description, location, and optional images.
    *   **Report Found Items:** Report items found on campus with mandatory image uploads for verification.
    *   **AI-Powered Search:** Search for items using natural language; the system uses semantic search to find relevant matches even if descriptions vary.
    *   **Smart Matching:** View automatically generated "Matches" with confidence scores indicating the likelihood of a match.
    *   **Match Management:** Review, Approve, or Reject potential matches.
    *   **Contact Exchange:** Upon mutual approval of a match, contact details are securely shared between the "Loser" and "Finder" to facilitate exchange.
    *   **Dashboard:** Track the status of reported items (Active, Resolved, Archived) and view match history.

3.  **Admin Capabilities:**
    *   **Centralized Dashboard:** View comprehensive analytics including total active cases, resolution rates, and daily report trends.
    *   **User Management:** View and manage registered users.
    *   **Item & Match Oversight:** Monitor all lost/found reports and match statuses across the platform.
    *   **Office Reporting:** Report items found and turned into the Admin Office directly, marking them as "Admin Reported".
    *   **Proxy Reporting:** Report items on behalf of students who might not have immediate access.

**Technology Behind FINDORA:**

*   **Backend Runtime & Framework:** Python 3.12+, FastAPI
*   **Frontend (Views):** Svelte 5, SvelteKit, TailwindCSS, shadcn-svelte
*   **Backend API Style:** REST (FastAPI with Pydantic models)
*   **Backend Architecture:** Monolithic with Modular Services
*   **Primary Database:** PostgreSQL with `pgvector` extension for vector similarity search
*   **AI/ML Engine:** `sentence-transformers` (Hugging Face) for generating text embeddings; `torch` for computation
*   **File Storage:** Local Server Filesystem (served via Static Files)
*   **Authentication:** OAuth2 with Password Flow (JWT), `passlib` for bcrypt hashing
*   **Key Libraries:**
    *   **Backend:** `sqlalchemy` (ORM), `alembic` (Migrations), `rapidfuzz` (Fuzzy string matching), `pillow` (Image processing).
    *   **Frontend:** `lucide-svelte` (Icons), `canvas-confetti` (UI effects), `zod` (Validation via `formsnap`).

**Real-World Applications:**

*   **University Campuses:** The primary use case, handling the high volume of lost personal items (ID cards, electronics, books) in a dense student population.
*   **Corporate Campuses:** Managing lost assets and personal items in large office complexes.
*   **Transport Hubs:** Can be adapted for airports or train stations to match passenger reports with found items.
*   **Event Venues:** Streamlining lost and found operations during large conferences or festivals.

**Future Scope:**

1.  **Mobile Application:** Develop native iOS and Android apps for easier on-the-go reporting and push notifications.
2.  **Real-Time Notifications:** Implement WebSockets or Server-Sent Events (SSE) to notify users instantly when a potential match is found.
3.  **Image Recognition:** Integrate computer vision to automatically tag and categorize items based on uploaded images (e.g., detecting "black wallet" from a photo).
4.  **Single Sign-On (SSO):** Integrate with university identity providers (LDAP/SAML/Google Workspace) for seamless login.
5.  **Smart Locker Integration:** Automate the physical exchange process by integrating with smart lockers, allowing users to drop off and pick up items securely without direct meetings.
6.  **Community Rewards:** Gamify the "Finder" experience with a reputation system or digital badges for helpful community members.
