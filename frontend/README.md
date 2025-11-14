# Lost & Found Frontend

A modern, beautiful frontend for the Lost & Found system built with Svelte 5, TailwindCSS, and shadcn-svelte.

## Features

- 🔐 **Authentication**: Login and registration with JWT token management
- 📦 **Item Management**: Report lost/found items with image uploads
- 🔍 **Search**: Search and filter found items
- ✅ **Match Management**: View and approve/reject matches
- 👨‍💼 **Admin Dashboard**: Comprehensive admin panel with analytics
- 🎨 **Beautiful UI**: Modern, responsive design with shadcn-svelte components

## Setup

1. Install dependencies:
```bash
pnpm install
```

2. Create a `.env` file (already created, but you can modify it):
```bash
# The .env file is already created with default values
# Edit frontend/.env to change the API URL if needed
VITE_API_BASE_URL=http://localhost:8000
```

3. Make sure the backend is running:
```bash
# In the backend directory
cd ../backend
uv run uvicorn app.main:app --reload
```

4. Start the frontend development server:
```bash
pnpm dev
```

The frontend will automatically connect to the backend at `http://localhost:8000` (or whatever you set in `.env`).

## Project Structure

```
src/
├── lib/
│   ├── api/          # API client utilities
│   ├── components/   # Reusable components
│   │   └── ui/       # shadcn-svelte components
│   └── stores/       # State management
└── routes/           # SvelteKit routes
    ├── login/        # Login page
    ├── register/     # Registration page
    └── dashboard/    # Main dashboard
        ├── found/    # Browse found items
        ├── report/   # Report items
        ├── matches/  # View matches
        └── admin/    # Admin dashboard
```

## API Integration

The frontend integrates with the FastAPI backend. All API calls are handled through the `$lib/api` modules with automatic token refresh.

## Technologies

- **Svelte 5**: Modern reactive framework with runes
- **SvelteKit**: Full-stack framework
- **TailwindCSS**: Utility-first CSS
- **shadcn-svelte**: Beautiful component library
- **TypeScript**: Type safety
