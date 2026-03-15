# Authentication and Admin System

## Overview

- **User roles**: `user` (default) and `admin`
- **Pages**: Login, Register, Profile (user and admin), Admin panel (admin only)

## First-time setup

### Create the first admin

**Option 1 – Environment variables (recommended for first run)**

Set before starting the backend:

- `INIT_ADMIN_EMAIL=admin@example.com`
- `INIT_ADMIN_PASSWORD=your-secure-password`

On first run, if no admin user exists, one will be created. Remove these env vars after the first run.

**Option 2 – Manual**

1. Register a normal user via the app (`/register`).
2. In MongoDB, set that user’s `role` to `admin` in the `users` collection.

### JWT secret (production)

Set a strong secret in production:

- `JWT_SECRET_KEY=your-long-random-secret`

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register (body: email, password, full_name?) |
| POST | `/auth/login` | Login (body: email, password) |
| POST | `/auth/logout` | Log logout (Bearer token) |
| GET/PUT | `/me` | Current user profile (Bearer token) |
| GET | `/admin/users` | List users (admin) |
| GET | `/admin/users/:id` | Get user (admin) |
| PUT | `/admin/users/:id` | Update user role/full_name (admin) |
| GET | `/admin/users/:id/sessions` | User’s chat sessions (admin) |
| GET | `/admin/users/:id/sessions/:sid` | Session history (admin) |
| GET | `/admin/activity-logs` | Activity logs (admin, query: user_id?, action?) |

## Frontend routes

- `/login` – Sign in  
- `/register` – Create account  
- `/profile` – My profile (requires login)  
- `/admin` – Admin dashboard (admin only)  
- `/admin/users` – User list  
- `/admin/users/:userId` – User detail + chat sessions/history  
- `/admin/activity-logs` – Activity logs  

## Activity logging

The following are logged when MongoDB is used:

- Login, logout, register  
- Chat messages (when user is logged in)  
- Admin: view users, view user, view history, view logs, update user  

Use **Activity Logs** in the admin panel to monitor these events.
