Fitbit Care / Corporate Wellness

The Fitbit Care category of your data export includes all of the content related to your Fitbit Care account.
This includes your corporate account information, engagement data and metrics.

Files Included:
----------

records.csv

This is the data related to FitbitCare user account.

    program_id                       - program id
    program_name                     - program name
    program_status                   - program status, e.g. ACTIVE, ENDED, etc
    record_start_date                - Date of start of user participation in the program
    record_end_date                  - Date of end of user participation in the program
    record_status                    - records status, e.g. ACTIVE, INACTIVE, etc

----------

tags.csv

This is the information about user tag in the FitbitCare program

    program_id                       - program id
    tag_name                         - tag name
    tag_value                        - tag value
    tag_status                       - tag status, e.g. ACTIVE, DELETED, etc

----------

Engagement Records.csv

This is the information about user engagement in the mindfulness, workout and guided programs

    timestamp                       - Timestamp when the event happened
    source                          - Source of the event
    status                          - Status of the event, e.g. STARTED, ENDED_EXPIRED, etc

----------

user_data.csv
This is the information about Fitbit Care user personal information

    programId                         - Fitbit Care program id
    first_name                        - First name
    last_name                         - Last name
    dateOfBirth                       - Data of birth
    corporate_email                   - Corporate email
    gender                            - Gender
    phone_number                      - Phone number
    employee_id                       - Employee id
    job_title                         - Job title
    custom_field                      - Additional information in case program onboarding process requests to fill custom fields
