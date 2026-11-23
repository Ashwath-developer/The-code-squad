# 🔥 Smart Fire Emergency Alert System

## Project Overview
Develop a web-based Smart Fire Emergency Alert System that helps colleges, universities, offices, and organizations report, monitor, and manage fire emergencies through a centralized platform.

The website should provide real-time emergency reporting, fire incident monitoring, location tracking, instant notifications, and emergency management through a user-friendly dashboard.

**This project is strictly software-based. It does not include hardware devices, sensors, GSM modules, or physical fire detection systems.**

## Objectives
- Provide a platform to report fire emergencies quickly.
- Notify registered users and emergency response teams.
- Display the location of reported fire incidents.
- Monitor active and resolved fire incidents.
- Help administrators manage emergency situations.
- Maintain a history of fire incidents for future analysis.

## Key Features

### 1. User Authentication
- User registration and login.
- Secure password management.
- Role-based access for users and administrators.

### 2. Emergency Reporting
- Report a fire emergency through the website.
- Enter incident location and description.
- Select fire severity level.
- Upload incident images.
- Generate a unique incident ID.

### 3. Live Emergency Dashboard
- Display active fire incidents.
- Show incident location on an interactive map.
- Display emergency status.
- Track incident updates.

### 4. Emergency Notifications
- Send email notifications to registered users and administrators.
- Display in-app emergency alerts.
- Notify relevant users based on their registered location or selected campus.
- Maintain notification history.

### 5. Admin Dashboard
- View all reported emergencies.
- Verify and manage incidents.
- Assign response personnel.
- Update emergency status.
- Manage users and notification settings.

### 6. Incident History and Reports
- Maintain previous emergency records.
- Filter incidents by date, location, and severity.
- Generate incident reports.
- Display statistics using charts.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python Flask |
| Database | MySQL |
| Maps | Leaflet.js / OpenStreetMap |
| Notifications | Email API / SMTP |
| Charts | Chart.js |
| Version Control | Git and GitHub |

## System Architecture

1. User interacts with the web application.
2. Flask backend processes user requests.
3. MySQL stores user and incident information.
4. Notification service sends emergency alerts.
5. Dashboard displays incident information and updates.

## Main Modules
- User Management
- Authentication
- Emergency Reporting
- Incident Management
- Location Management
- Notification Management
- Admin Dashboard
- Reports and Analytics

## Installation and Setup

### Prerequisites
- Python 3.x
- MySQL Server
- Visual Studio Code
- Git

### Installation

Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Navigate to the project folder:

```bash
cd fire-alert-system
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure your MySQL database and environment variables.

Run the application:

```bash
python app.py
```

Open your browser:

```text
http://127.0.0.1:5000
```

## Future Enhancements
- Mobile application integration.
- SMS and push notification support.
- AI-based fire incident severity analysis.
- Advanced location-based emergency notifications.
- Integration with official emergency response services.

## Project Scope
This project focuses exclusively on a software-based fire emergency reporting, notification, and management platform. Fire incidents are reported manually by users through the website. The system does not automatically detect fires.

## Disclaimer
This platform is an academic/software prototype and is not a replacement for certified fire detection systems or official emergency response services.

## License
This project is developed for academic and educational purposes.

