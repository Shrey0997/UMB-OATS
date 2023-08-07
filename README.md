# UMB-OATS
## Online Application for Tutoring Scheduling
### University of Massachusetts, Boston

## Project Overview

UMB-OATS is a scheduling application built with Django, HTML and bootstrap. It allows students to book tutoring sessions and manage their schedules.

## Setting up

To set up the project, follow these steps:

1. Clone the repository to your local machine.
2. Navigate to the directory where the `manage.py` file is located.
3. (Optional) Create a virtual environment for the project (recommended).
4. Activate the virtual environment.
5. Install the required packages by running the following command:
   - pip install -r requirements.txt
6. Start the application locally by running the following command:
   - python manage.py runserver


Make sure to replace `python` with the appropriate command for your Python environment.

## Project Structure

The project consists of the following main files:

- `settings.py`: Contains the configuration settings for the Django project.
- `urls.py`: Defines the URL patterns and corresponding views for the application.
- `views.py`: Contains the view functions that handle requests and generate responses.
- `models.py`: Contains the models to represent the structure in the database

## Features
1. User registration and authentication: 
   - Users can sign up for an account and log in to the application.
2. User roles and permissions: 
   - Different roles such as student and tutor can be assigned to users, granting them specific permissions.
3. Tutor availability management: 
   - Tutors can set their availability for tutoring sessions, specifying the dates and time slots they are available.
4. Session booking: 
   - Students can browse available tutoring sessions and book sessions with tutors based on their availability.
5. Session cancellation: 
   - Both students and tutors can cancel booked sessions, triggering notifications to the affected parties.
6. Semester management: 
   - Administrators can add and manage academic semesters, defining start and end dates for each semester.
7. Password management: 
   - Users can change their passwords through a secure password change form.
8. Session history: 
   - Users can view their session history, including past sessions they have participated in.
9. Email notifications: 
   - Automated email notifications are sent to users for various actions such as session booking, cancellation, and password reset.
10. Error handling: 
    - Custom error pages and handling for 404 (Page Not Found) errors to enhance user experience.

Please refer to the individual files for more detailed information and code documentation.

