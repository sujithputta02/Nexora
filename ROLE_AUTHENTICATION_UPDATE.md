# Role Authentication System Update

## Overview
Updated the NEXORA web application to support all four RBAC roles with persistent authentication across page refreshes.

## Changes Made

### 1. Backend (app/app.py)
- **Added Public role to login system**: Added "public" user with "guest" password to the USERS dictionary
- All four roles now have login credentials:
  - `scientist` / `isro123` → Scientist role
  - `engineer` / `tech456` → Engineer role  
  - `analyst` / `data789` → Analyst role
  - `public` / `guest` → Public role

### 2. Frontend (app/templates/index.html)

#### Role Selector Dropdown
The dropdown already had all four roles available:
- Public
- Analyst
- Engineer
- Scientist

#### Authentication Persistence System
Implemented a comprehensive authentication state management system:

**New Features:**
1. **LocalStorage Persistence**:
   - Authentication state is saved to `localStorage` with key `nexora_auth`
   - Stores authenticated roles in a Set
   - Saves the last selected role
   - Persists across page refreshes and browser restarts

2. **Multi-Role Authentication**:
   - Users can authenticate for multiple roles in the same session
   - Each role maintains its own authentication state
   - Switching between authenticated roles doesn't require re-login

3. **Session Restoration**:
   - `restoreAuthState()` function called on page load
   - Restores last selected role
   - Restores all authenticated roles
   - Shows logout button if user is in an authenticated role

4. **Smart Role Switching**:
   - Public role: No authentication required
   - Non-Public roles: Requires authentication if not already authenticated
   - Confirmation prompt when switching from authenticated role to Public
   - Seamless switching between already-authenticated roles

5. **Logout Functionality**:
   - Logout button visible only for authenticated (non-Public) roles
   - Clicking logout clears ALL authenticated roles
   - Returns user to Public role
   - Clears localStorage
   - Confirmation message displayed

#### Updated Functions

**New Functions:**
- `restoreAuthState()`: Restores authentication from localStorage on page load
- `saveAuthState()`: Saves current authentication state to localStorage
- `requiresAuth(role)`: Checks if a role requires authentication
- `isAuthenticated(role)`: Checks if user is authenticated for a specific role

**Updated Functions:**
- `submitLogin()`: Now handles authentication for any role (not just Scientist)
- `logout()`: Clears all authenticated roles and returns to Public
- Role change handler: Implements smart switching logic with persistence

**Updated UI Elements:**
- Login modal title changed from "Scientist Access" to "Secure Access"
- Modal description updated to be role-agnostic
- Logout button shows/hides based on authentication state
- Logout button styled with red theme for visibility

## User Credentials

| Username  | Password | Role     | Access Level |
|-----------|----------|----------|-------------|
| public    | guest    | Public   | Public documents only |
| analyst   | data789  | Analyst  | Mission stats + Public |
| engineer  | tech456  | Engineer | Technical + Mission stats + Public |
| scientist | isro123  | Scientist| All documents including classified |

## User Experience

### First Time Login:
1. User opens application → Defaults to Public role
2. User selects Engineer role → Login modal appears
3. User enters credentials → Authenticated as Engineer
4. Logout button appears
5. User can now switch to any authenticated role

### After Page Refresh:
1. Application restores last selected role
2. Authentication state is preserved
3. User remains logged in to all previously authenticated roles
4. No re-authentication required

### Switching Roles:
- **To authenticated role**: Instant switch if already authenticated, otherwise shows login modal
- **To Public from authenticated role**: Confirmation prompt (to prevent accidental logout)
- **Between authenticated roles**: Instant switch with no re-authentication

### Logout:
- Clears all role authentications at once
- Returns to Public role
- Requires fresh login for any non-Public role access

## Security Considerations

1. **Client-Side Storage**: Authentication state is stored in localStorage (client-side)
   - For production: Consider server-side session management with secure tokens
   - Current implementation suitable for demo/local deployment

2. **Role Separation**: Each role maintains separate sessions and document access
   - RBAC enforced at backend level
   - Frontend role switching updates query context

3. **Logout Behavior**: Complete logout clears all roles
   - Prevents partial authentication states
   - Clean slate for new user sessions

## Testing Checklist

- [x] All four roles appear in dropdown
- [x] Login works for all roles
- [x] Authentication persists across page refresh
- [x] Logout clears all authenticated roles
- [x] Role switching works without re-authentication
- [x] Public role accessible without login
- [x] Confirmation prompt when switching from authenticated to Public
- [x] Logout button visibility matches authentication state
- [x] Sessions load correctly for each role
- [x] Document access respects role permissions

## Future Enhancements

1. **Server-Side Sessions**: Move authentication to server with JWT tokens
2. **Session Timeout**: Auto-logout after period of inactivity
3. **Remember Me**: Option to persist authentication longer-term
4. **Role Indicators**: Visual badges showing current role clearance level
5. **Activity Logging**: Track role switches and authentication events
