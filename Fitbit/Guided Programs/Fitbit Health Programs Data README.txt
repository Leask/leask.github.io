Fitbit Health Programs

The Fitbit Care category of your data export includes all of the content related to your Fitbit Health Programs
connected to your account.
This includes your health programs data, tasks data in particular programs

Files Included:
----------

{PROGRAM_ID}_{PROGRAM_CREATED_DATE}.json

File names include the next data:
    PROGRAM_ID                       - Program id
    PROGRAM_CREATED_DATE             - Date of start of user participation in the program

File content is json that includes the next data related to the health programs:


    summary                          - Summary of the health program
    state                            - Actual state of the health program.
    tasks                            - List of tasks that connected to particular health programs

Where summary included the next data:

    title                            - Subtitle of the health program
    subtitle                         - Subtitle of the health program
    status                           - Actual health program status, e.g. ACTIVE, COMPLETE, etc
    startedAt                        - Date of start of user participation in the health program
    endedAt                          - Date of end of user participation in the health program
    detail                           - Details of the health program

Where each task in the tasks list include the next data:

    id                               - Health Task id
    title                            - Title of the health task
    subtitle                         - Subtitle of the health task
    status                           - Actual health task status, e.g. ACTIVE, COMPLETED, OBSOLETE
    dataJson                         - Specific data for the health task related to health program
    dueDate                          - Due date for health task

------------------
