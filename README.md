# Course Planner Application

A comprehensive course planning application that helps students optimize their academic schedules using mathematical optimization and AI-powered recommendations.

## 🏗️ Clean Architecture

The application follows a **clean, modular architecture** with clear separation of concerns:

### **Core Principles**
- **Single Responsibility**: Each class has one clear purpose
- **Dependency Injection**: Services accept repositories as parameters
- **Separation of Concerns**: Routes, services, and data access are clearly separated
- **Testability**: Business logic is isolated and easily testable

### **Architecture Layers**

1. **Presentation Layer** (`backend/app/routes/`)
   - Web routes for user interface
   - API routes for programmatic access
   - Clean request/response handling

2. **Business Logic Layer** (`backend/core/services/`)
   - `ScheduleService`: Course planning business logic
   - `AIService`: AI-powered recommendations
   - Pure business logic, no framework dependencies

3. **Data Access Layer** (`backend/core/data/`)
   - `CourseRepository`: Course data access
   - `UserRepository`: User data and preferences
   - Abstracted data access with caching

4. **Infrastructure Layer** (`backend/core/scheduler/`)
   - `CourseScheduler`: Mathematical optimization engine
   - Gurobi integration for constraint solving

## 📁 Project Structure

```
courses-planner/
├── backend/                        # Backend application
│   ├── app/                       # Flask application layer
│   │   ├── __init__.py            # Application factory
│   │   ├── main_app.py            # Main web application
│   │   ├── api_app.py             # REST API application
│   │   └── routes/                # Route handlers
│   │       ├── web_routes.py      # Web interface routes
│   │       └── api_routes.py      # REST API routes
│   ├── core/                      # Business logic core
│   │   ├── services/              # Business services
│   │   │   ├── schedule_service.py # Course scheduling logic
│   │   │   └── ai_service.py      # AI integration
│   │   ├── data/                  # Data access layer
│   │   │   ├── course_repository.py # Course data access
│   │   │   └── user_repository.py # User data access
│   │   └── scheduler/             # Optimization engine
│   │       └── course_scheduler.py # Mathematical optimization
│   ├── models/                    # Data models (legacy)
│   │   ├── scheduler_data.py      # Course plans and time data
│   │   └── fall25_courses_data.py # Fall 2025 course offerings
│   ├── utils/                     # Utility functions
│   │   └── mcp_fixed_section.py   # MCP integration utilities
│   ├── config/                    # Configuration files
│   │   ├── settings.py            # Application settings
│   │   └── openai_key.py          # OpenAI API key (gitignored)
│   └── tests/                     # Test files
│       └── test_scheduler.py      # Scheduler tests
├── frontend/                      # Frontend assets
│   ├── templates/                 # HTML templates
│   │   ├── index.html             # Main page
│   │   ├── plan.html              # Course plan display
│   │   └── schedule.html          # Timetable display
│   └── static/                    # Static assets
│       ├── css/                   # Stylesheets
│       └── js/                    # JavaScript files
├── database/                      # Data storage
│   ├── courses_fall25/            # Fall 2025 course data files
│   ├── scripts/                   # Data generation scripts
│   │   └── generate_fall25_courses.py
│   ├── last_plan.json             # Last generated plan
│   └── fixed_courses.json         # Fixed course assignments
├── docs/                          # Documentation
├── run_server.py                  # Server runner script
├── setup.py                       # Setup automation script
├── requirements.txt               # Python dependencies
├── env.example                    # Environment variables template
└── README.md                      # This file
```

## 🚀 Features

- **Intelligent Course Scheduling**: Uses mathematical optimization (Gurobi) to create optimal course schedules
- **AI-Powered Recommendations**: Integrates with OpenAI for intelligent course suggestions
- **Prerequisite Management**: Automatically handles course prerequisites and dependencies
- **Flexible Planning**: Supports custom course loads and semester preferences
- **Interactive Interface**: Modern web interface for easy course planning
- **Data-Driven**: Based on real course data from Fall 2025
- **Clean Architecture**: Modular, maintainable, and testable codebase
- **Separation of Concerns**: Clear boundaries between presentation, business logic, and data access
- **Dependency Injection**: Loosely coupled components for better testability
- **RESTful API**: Programmatic access to all features

## 🛠️ Technology Stack

### Backend
- **Flask**: Web framework
- **Gurobi**: Mathematical optimization solver
- **OpenAI API**: AI-powered recommendations
- **Python-dotenv**: Environment variable management

### Frontend
- **HTML5/CSS3**: Modern web interface
- **JavaScript**: Interactive functionality
- **Bootstrap**: Responsive design framework

### Data
- **JSON**: Course data storage
- **File-based**: Simple data persistence

## 📋 Prerequisites

- Python 3.8 or higher
- Gurobi optimization solver license
- OpenAI API key

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd courses-planner
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=your_secret_key_here
   FLASK_DEBUG=True
   ```

5. **Install Gurobi**
   - Download and install Gurobi from [gurobi.com](https://www.gurobi.com/)
   - Obtain a license (academic licenses are free)
   - Install the Python package: `pip install gurobipy`

## 🚀 Running the Application

### Option 1: Using the run script (recommended)
```bash
# Run the main web server (default)
python run_server.py

# Run the REST API server
python run_server.py --server api

# Run with custom host and port
python run_server.py --host 0.0.0.0 --port 8080 --debug
```

### Option 2: Direct application execution
```bash
# Run main web application directly
python backend/app/main_app.py

# Run API application directly
python backend/app/api_app.py
```

### Option 3: Using the application factory
```bash
# Run with custom configuration
python -c "from backend.app import create_app; app = create_app(); app.run(debug=True)"
```

### Access the application
Open your browser and navigate to `http://localhost:5000`

## 📖 Usage

1. **Select Your Major**: Choose your academic major from the dropdown
2. **Enter Completed Courses**: List courses you've already completed
3. **Set Semester Progress**: Indicate how many semesters you've completed
4. **Generate Plan**: Click to generate an optimized course schedule
5. **Review and Adjust**: View the generated plan and make adjustments as needed

## 🧪 Testing

Run the test suite:
```bash
cd backend
python -m pytest tests/
```

## 📁 Key Components

### **Backend Architecture**

#### **Application Layer** (`backend/app/`)
- **Application Factory**: Clean Flask app creation with dependency injection
- **Web Routes**: User interface endpoints with clean request handling
- **API Routes**: RESTful endpoints for programmatic access
- **Main Apps**: Separate applications for web and API servers

#### **Business Logic Layer** (`backend/core/services/`)
- **ScheduleService**: Course planning business logic with dependency injection
- **AIService**: AI-powered recommendations with OpenAI integration
- **Pure Business Logic**: Framework-independent, easily testable services

#### **Data Access Layer** (`backend/core/data/`)
- **CourseRepository**: Abstracted course data access with caching
- **UserRepository**: User data and preferences management
- **Repository Pattern**: Clean data access abstraction

#### **Infrastructure Layer** (`backend/core/scheduler/`)
- **CourseScheduler**: Mathematical optimization engine using Gurobi
- **Constraint Solving**: Advanced optimization algorithms for course scheduling

### **Frontend Components**

- **Home Page**: Course selection and plan generation
- **Plan View**: Detailed course plan visualization
- **Schedule View**: Semester-by-semester breakdown

### **Data Storage**

- **Course Data**: JSON files containing course information
- **User Plans**: Saved course plans and preferences
- **Scripts**: Data generation and migration utilities

## 🏆 Benefits of Clean Architecture

### **Maintainability**
- **Single Responsibility**: Each class has one clear purpose
- **Modular Design**: Easy to find and modify specific functionality
- **Clear Interfaces**: Well-defined contracts between components

### **Testability**
- **Isolated Business Logic**: Services can be unit tested independently
- **Mockable Dependencies**: Easy to mock repositories and external services
- **Framework Independence**: Business logic doesn't depend on Flask

### **Scalability**
- **Easy to Extend**: New features can be added without affecting existing code
- **Clear Structure**: New developers can quickly understand the codebase
- **Loose Coupling**: Components can be modified independently

### **Code Quality**
- **Consistent Naming**: Clear, descriptive function and class names
- **Type Hints**: Better IDE support and code documentation
- **Error Handling**: Proper exception handling throughout the application

## 🔒 Security

- API keys are stored in environment variables
- Sensitive configuration is kept separate from code
- Input validation on all user inputs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation in the `docs/` folder
- Review the test files for usage examples

## 🔄 Version History

- **v1.0.0**: Initial release with basic course scheduling
- **v1.1.0**: Added AI-powered recommendations
- **v1.2.0**: Improved optimization algorithms
- **v2.0.0**: Complete restructuring with modular architecture 