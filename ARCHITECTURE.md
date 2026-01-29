# CineLog Backend - Architecture

## Project Structure

The application follows a **3-layer architecture**:

### 1. **Presentation Layer** (`main.py`)
- FastAPI route handlers
- Request/response validation using Pydantic schemas
- HTTP status codes and error handling
- Delegates all business logic to the business logic layer

### 2. **Business Logic Layer** (`business_logic.py`)
- Orchestrates data access operations
- Coordinates between multiple data access functions
- Transforms data for API responses
- Implements business rules and workflows
- Examples: `process_swipe()`, `get_deck()`, `send_friend_request()`

### 3. **Data Access Layer** (`data/`)
Separated into **read** and **write** operations:

#### `data/read/` - Query Operations (SELECT)
- `users.py` - User lookups, friendship queries
- `movies.py` - Movie/genre queries
- `lists.py` - Master list and watch later list queries
- `__init__.py` - Exports all read functions

#### `data/edit/` - Mutation Operations (INSERT, UPDATE, DELETE)
- `users.py` - User creation/management
- `movies.py` - Movie/genre creation and syncing
- `swipes.py` - Swipe creation
- `lists.py` - Master list and watch later list operations
- `friendships.py` - Friendship creation and deletion
- `__init__.py` - Exports all edit functions

## Key Benefits

✅ **Separation of Concerns** - Each layer has a single responsibility  
✅ **Reusability** - Business logic functions can be used by multiple routes  
✅ **Testability** - Easy to unit test each layer independently  
✅ **Maintainability** - Changes to data access don't affect routes  
✅ **Clarity** - Clear data flow: Route → Business Logic → Data Access → Database  

## Data Flow Example

```
User sends HTTP request
    ↓
main.py (validate request)
    ↓
business_logic.py (orchestrate, transform)
    ↓
data/read/ + data/edit/ (access database)
    ↓
Database
```

## File Organization

- **models.py** - SQLAlchemy ORM models
- **schemas.py** - Pydantic request/response models
- **utils.py** - Utility functions (cursor encoding/decoding, etc.)
- **db.py** - Database connection and session management

## Adding New Features

1. Create read/edit functions in `data/read/` or `data/edit/`
2. Create business logic function in `business_logic.py`
3. Add route handler in `main.py` that calls the business logic function
4. Export new functions in `data/read/__init__.py` or `data/edit/__init__.py`
