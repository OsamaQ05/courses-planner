# Course Planner Architecture

## Overview

The Course Planner application follows a modular, layered architecture that separates concerns between frontend, backend, and data layers. This document outlines the architectural decisions and component interactions.

## Architecture Layers

### 1. Presentation Layer (Frontend)
- **Location**: `frontend/`
- **Components**: HTML templates, CSS styles, JavaScript
- **Responsibility**: User interface and user experience
- **Technology**: HTML5, CSS3, JavaScript, Bootstrap

### 2. Application Layer (Backend)
- **Location**: `backend/`
- **Components**: Flask application, API routes, business logic
- **Responsibility**: Request handling, business logic, data processing
- **Technology**: Flask, Python

### 3. Data Layer (Database)
- **Location**: `database/`
- **Components**: JSON files, data scripts, migrations
- **Responsibility**: Data storage and retrieval
- **Technology**: JSON, file-based storage

## Component Breakdown

### Backend Structure

```
backend/
├── app/                    # Flask application core
│   ├── server.py          # Main Flask application
│   └── server2.py         # Alternative implementation
├── api/                   # API endpoints
├── models/                # Data models and schemas
├── services/              # Business logic services
├── utils/                 # Utility functions
├── config/                # Configuration management
└── tests/                 # Test suite
```

#### App Module
- **Purpose**: Core Flask application setup and configuration
- **Key Files**:
  - `server.py`: Main application with routes and business logic
  - `server2.py`: Alternative implementation for comparison

#### API Module
- **Purpose**: RESTful API endpoints
- **Responsibilities**:
  - Handle HTTP requests
  - Validate input data
  - Return structured responses

#### Models Module
- **Purpose**: Data structure definitions
- **Key Files**:
  - `scheduler_data.py`: Course scheduling data models
  - `fall25_courses_data.py`: Course catalog data

#### Services Module
- **Purpose**: Business logic implementation
- **Key Files**:
  - `scheduler.py`: Course scheduling optimization service
- **Responsibilities**:
  - Mathematical optimization
  - Course planning algorithms
  - Business rule enforcement

#### Utils Module
- **Purpose**: Reusable utility functions
- **Key Files**:
  - `mcp_fixed_section.py`: MCP protocol utilities

#### Config Module
- **Purpose**: Application configuration management
- **Key Files**:
  - `settings.py`: Centralized configuration
  - `openai_key.py`: API key management

### Frontend Structure

```
frontend/
├── templates/             # HTML templates
│   ├── index.html        # Home page
│   ├── plan.html         # Course plan view
│   └── schedule.html     # Schedule view
└── static/               # Static assets
    ├── css/              # Stylesheets
    └── js/               # JavaScript files
```

### Database Structure

```
database/
├── courses_fall25/       # Course data files
├── migrations/           # Database migrations
├── scripts/              # Data generation scripts
├── last_plan.json        # User plan storage
└── fixed_courses.json    # Fixed course assignments
```

## Data Flow

### 1. User Request Flow
```
User Input → Frontend → Backend API → Services → Models → Database
```

### 2. Response Flow
```
Database → Models → Services → Backend API → Frontend → User
```

### 3. Optimization Flow
```
Course Data → Scheduler Service → Gurobi Solver → Optimized Plan → Response
```

## Key Design Principles

### 1. Separation of Concerns
- **Frontend**: Only handles presentation and user interaction
- **Backend**: Handles business logic and data processing
- **Database**: Handles data storage and retrieval

### 2. Modularity
- Each component has a single responsibility
- Components are loosely coupled
- Easy to test and maintain individual components

### 3. Configuration Management
- Centralized configuration in `backend/config/settings.py`
- Environment-based configuration
- Secure handling of sensitive data

### 4. Error Handling
- Consistent error responses across API endpoints
- Proper logging and debugging information
- User-friendly error messages

## Security Considerations

### 1. API Key Management
- API keys stored in environment variables
- Separate configuration for development and production
- No hardcoded secrets in source code

### 2. Input Validation
- All user inputs validated on both frontend and backend
- SQL injection prevention (though using JSON files)
- XSS prevention through proper output encoding

### 3. File Access
- Restricted access to sensitive files
- Proper file permissions
- Secure file handling

## Performance Considerations

### 1. Optimization
- Gurobi solver for mathematical optimization
- Efficient data structures for course planning
- Caching of frequently accessed data

### 2. Scalability
- Modular architecture allows for easy scaling
- Stateless API design
- File-based storage can be replaced with database

## Testing Strategy

### 1. Unit Tests
- Individual component testing
- Service layer testing
- Utility function testing

### 2. Integration Tests
- API endpoint testing
- End-to-end workflow testing
- Data flow testing

### 3. Performance Tests
- Optimization algorithm testing
- Load testing for concurrent users

## Deployment Considerations

### 1. Environment Setup
- Virtual environment for Python dependencies
- Environment-specific configuration
- Proper dependency management

### 2. Production Deployment
- WSGI server (e.g., Gunicorn)
- Reverse proxy (e.g., Nginx)
- Process management (e.g., systemd)

### 3. Monitoring
- Application logging
- Performance monitoring
- Error tracking

## Future Enhancements

### 1. Database Migration
- Replace JSON files with proper database
- Implement database migrations
- Add data validation and constraints

### 2. API Enhancement
- RESTful API design
- API versioning
- Rate limiting and authentication

### 3. Frontend Improvements
- Single Page Application (SPA)
- Modern JavaScript framework
- Progressive Web App (PWA) features

### 4. Advanced Features
- Multi-user support
- Course recommendation engine
- Integration with university systems 