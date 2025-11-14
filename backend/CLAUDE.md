### 🚀 Project Specification: AI-Powered University Lost & Found System

**Project Goal:** Develop a comprehensive API-first, AI-powered "Lost and Found" system for a university campus using FastAPI, PostgreSQL, and Transformer models. The system will feature distinct user/admin roles, a robust authentication system, and an intelligent matching engine based on vector similarity search for both text and images.

---

### Core Technologies

* **Backend:** FastAPI
* **Database:** PostgreSQL with the **`pgvector`** extension (for native vector storage and similarity search).
* **Authentication:** JWT (JSON Web Tokens) via FastAPI's `OAuth2PasswordBearer` and `passlib` for password hashing.
* **AI Model (Multimodal):** `sentence-transformers/clip-ViT-B-32`. This single model will be used to generate embeddings for **both** text descriptions and images, allowing them to be compared in the same vector space.
* **Data Validation:** Pydantic (for API request/response models) or SQLModel (for combined DB and Pydantic models).
* **Async Tasks:** FastAPI's `BackgroundTasks` (or Celery/Redis for a larger-scale deployment) to handle non-blocking AI embedding generation and notification dispatch.
* **File Storage:** A solution for storing uploaded images (e.g., a local `/static/uploads`-like folder or a cloud bucket like S3).

---

### 1. Database & Data Models

Three core tables are required:

1.  **`User` Model:**
    * `id` (UUID, Primary Key)
    * `name` (String)
    * `email` (String, Unique)
    * `hashed_password` (String)
    * `roll_number` (String, Unique)
    * `hostel` (String, Nullable)
    * `contact_number` (String)
    * `role` (Enum: `USER`, `ADMIN`, default: `USER`)
    * `created_at` (DateTime)

2.  **`Item` Model:**
    * `id` (UUID, Primary Key)
    * `reported_by_user_id` (ForeignKey -> `User.id`)
    * `status` (Enum: `LOST`, `FOUND`)
    * `description` (Text)
    * `location` (String)
    * `image_url` (String, Nullable for `LOST`, Required for `FOUND`)
    * **`description_vector`** (Vector, from CLIP text embedding)
    * **`image_vector`** (Vector, from CLIP image embedding, Nullable for `LOST`)
    * `is_active` (Boolean, default: `True`) - *Set to `False` when archived/resolved.*
    * `is_admin_report` (Boolean, default: `False`) - *To track items reported by admin.*
    * `reported_at` (DateTime)

3.  **`Match` Model:**
    * `id` (UUID, Primary Key)
    * `lost_item_id` (ForeignKey -> `Item.id` where `status`='LOST')
    * `found_item_id` (ForeignKey -> `Item.id` where `status`='FOUND')
    * `confidence_score` (Float) - *The calculated similarity score.*
    * `match_status` (Enum: `PENDING`, `APPROVED`, `REJECTED`, default: `PENDING`)
    * `created_at` (DateTime)

---

### 2. User Authentication & Roles

* **Endpoints:**
    * `POST /auth/register`: Creates a new user with the `USER` role.
    * `POST /auth/login`: Takes email/password, returns an access token.
    * `GET /users/me`: A protected endpoint to get the current user's details.
* **Authorization:**
    * **User Role:** Can report items, view their own items, view their "pending" matches, and approve a match for an item they lost.
    * **Admin Role:** Full CRUD access on all users and items. Can access the analytics dashboard. Can report items on behalf of other users or the admin office.

---

### 3. Core Feature: Item Reporting & AI Matching

This is the central workflow.

#### Step 1: Reporting an Item (Lost or Found)

* `POST /items/report_lost` (Protected, User)
    * **Request:** `description: str`, `location: str`, `image: UploadFile | None`
    * **Logic:**
        1.  Validate input.
        2.  Generate `description_vector` using CLIP's text model.
        3.  If `image` is provided, save it and generate `image_vector` using CLIP's image model.
        4.  Save the new `Item` to the database (`status='LOST'`, `is_active=True`).
        5.  Trigger background task: `run_matching_algorithm(new_item_id)`.
* `POST /items/report_found` (Protected, User)
    * **Request:** `description: str`, `location: str`, `image: UploadFile` (**Image is mandatory**)
    * **Logic:**
        1.  Validate input (image must exist).
        2.  Generate `description_vector` (CLIP text).
        3.  Save image, generate `image_vector` (CLIP image).
        4.  Save the new `Item` (`status='FOUND'`, `is_active=True`).
        5.  Trigger background task: `run_matching_algorithm(new_item_id)`.

#### Step 2: The AI Matching Algorithm (Background Task)

This function runs asynchronously after any new item is added.

* `def run_matching_algorithm(new_item_id: UUID):`
    1.  Fetch the `new_item` (e.g., a `LOST` item).
    2.  Identify the target pool: All `FOUND` items where `is_active=True`. (If `new_item` is `FOUND`, target pool is `LOST` items).
    3.  Iterate through each `target_item` in the pool:
        * Calculate multiple similarity scores (using cosine similarity from `pgvector`):
            * `score_text_text` = `sim(new_item.desc_vector, target_item.desc_vector)`
            * `score_text_image` = `sim(new_item.desc_vector, target_item.image_vector)`
            * `score_image_text` = `sim(new_item.image_vector, target_item.desc_vector)` (if `new_item` has image)
            * `score_image_image` = `sim(new_item.image_vector, target_item.image_vector)` (if `new_item` has image)
        * **Calculate `final_score`:** Take the **maximum** of all calculated scores.
            * `final_score = max(score_text_text, score_text_image, score_image_text, score_image_image)`
    4.  **Create Match:**
        * If `final_score >= 0.65` (65% confidence):
            * Create a new `Match` entry in the database linking the `lost_item_id` and `found_item_id` with the `final_score` and `match_status='PENDING'`.
            * Trigger notifications (email + dashboard) to both the `loser` and the `finder`.

---

### 4. Core Feature: Match Resolution & Notifications

#### Step 1: Viewing Matches

* `GET /matches/my_matches` (Protected, User)
    * **Logic:** Returns a list of all matches where the `lost_item_id` belongs to the current user and `match_status='PENDING'`.
    * **Response:** Should include full details of the *found item* (description, image, location) for the user to review.
* `GET /items/all_found_items` (Protected, User)
    * **Logic:** Returns a view of *all* `FOUND` items where `is_active=True`. This allows users to browse manually.

#### Step 2: Approving a Match

* `POST /matches/{match_id}/approve` (Protected, User)
    * **Auth:** Must verify the current user is the owner of the `lost_item` in this match.
    * **Logic:**
        1.  Set `Match.match_status = 'APPROVED'`.
        2.  **Archive both items:**
            * Set `Item.is_active = False` for the `lost_item`.
            * Set `Item.is_active = False` for the `found_item`.
        3.  Trigger background task: `send_resolution_notifications(match_id)`.

#### Step 3: Resolution Notification (Background Task)

* `def send_resolution_notifications(match_id: UUID):`
    1.  Fetch the `match`, the `lost_item` (and its reporter, the `loser`), and the `found_item` (and its reporter, the `finder`).
    2.  **Determine Finder's Contact:**
        * If `found_item.is_admin_report == True`:
            * `finder_contact_details` = "The Campus Admin Office (Location: ..., Phone: ...)"
        * Else:
            * `finder_contact_details` = `finder.name`, `finder.email`, `finder.contact_number`
    3.  **Determine Loser's Contact:**
        * If `lost_item.is_admin_report == True`:
            * `loser_contact_details` = "The Campus Admin Office"
        * Else:
            * `loser_contact_details` = `loser.name`, `loser.email`, `loser.contact_number`
    4.  **Send Notifications:**
        * **To Loser:** "Your item has been found! Please contact: [finder_contact_details]"
        * **To Finder:** "The item you found has been claimed by its owner. They will be contacting you. [loser_contact_details]"
        * *(Note: Share details with both parties as requested, or adjust if privacy is a concern).*

---

### 5. Admin Portal & Special Workflows

* `POST /admin/report_on_behalf` (Protected, Admin)
    * **Request:** `user_identifier: str` (email or roll no), `item_status: 'LOST' | 'FOUND'`, plus all other item details (desc, location, image).
    * **Logic:**
        1.  Look up the user by `user_identifier`.
        2.  Create the `Item` record, linking it to the found `user.id`.
        3.  Set `is_admin_report = True`.
        4.  This item enters the normal matching flow.
* `POST /admin/report_office_item` (Protected, Admin)
    * **Request:** `item_status: 'FOUND'`, plus item details.
    * **Logic:**
        1.  Create the `Item` record.
        2.  Link `reported_by_user_id` to the *admin's own user ID*.
        3.  Set `is_admin_report = True`.
* `GET /admin/dashboard/analytics` (Protected, Admin)
    * **Response:**
        * Total users, items (lost/found/resolved).
        * Graphs/data of items reported over time.
* `GET /admin/dashboard/users` (Protected, Admin)
    * **Response:** Paginated table of all `User` data.
* `GET /admin/dashboard/items` (Protected, Admin)
    * **Response:** Paginated table of all `Item` data (both active and archived).
* `GET /admin/dashboard/matches` (Protected, Admin)
    * **Response:** Paginated table of all `Match` data (pending, approved, etc.).

This is a very comprehensive specification that covers **all the core requirements** you outlined in your original prompt.

It successfully translates your ideas into a formal structure with:
* Clear **database models** (User, Item, Match).
* A specific **AI strategy** (using a single CLIP model for multimodal search).
* A robust **matching algorithm** (checking all combinations and taking the `max` score).
* Distinct **User vs. Admin roles** and permissions.
* The complete **workflow for Admin-reported items** and how contact details are handled.
* The **archiving flow** (`is_active = False`) to remove resolved items from matching.

---

### 6. Match Management: Rejection & Manual Resolution

* **Match Rejection:** The spec includes an `approve` endpoint, and the `Match` model has a `REJECTED` status. You should also add an endpoint: `POST /matches/{match_id}/reject`. This allows a user to clear their dashboard of bad matches.
* **Manual Resolution (by User):** What if a user finds their item *without* using the system? They should be able to manually close their own report.
    * **Endpoint:** `POST /items/{item_id}/resolve`
    * **Logic:** The user (who must be the owner) can mark their own `LOST` or `FOUND` item as resolved, which sets `is_active = False` and archives it.

### 7. Enhanced Search & Filtering

* **Keyword Search:** The current system is 100% AI vector search. You might also want a traditional keyword search (e.g., "lost red keychain near library"). This can be a separate endpoint (`GET /items/search`) that uses standard SQL `LIKE` or full-text search on the `description` and `location` fields.
* **Filtering:** Users might want to filter the `GET /items/all_found_items` list.
    * **Endpoint:** `GET /items/all_found_items?location=library&date_after=...`

### 8. Real-Time Dashboard Updates

* Your prompt says "show each and every update to the dashboard too." The current spec supports this by providing endpoints like `/matches/my_matches` that the frontend can call.
* **For a truly instant update:** You could implement **WebSockets** or **Server-Sent Events (SSE)** with FastAPI. When a new `Match` is created in the database, the server could *push* a notification to the relevant users' dashboards in real-time.

### 9. Security & Privacy

* **Rate Limiting:** To prevent abuse (e.g., a bot spamming item reports), you should implement rate limiting (e.g., using `fastapi-limiter`) on the `/items/report_...` and `/auth/register` endpoints.

---
