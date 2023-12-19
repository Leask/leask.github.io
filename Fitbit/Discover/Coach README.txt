Coach Data Export

The Coach category of your data export includes the pieces of content that you favorited in the Coach view, as well as
content recommendations that were generated for you based on watch history, wellbeing and physical activity.

Files included:
----------

Coach Favorites.csv

This includes the items that you marked as favorite in the Coach view.
   timestamp                       - Datetime of the moment the item was favorited
   id                              - Unique identifier of the item
   title                           - Name of the item
   bundle_id                       - Category of content in the Coach view that the item belongs to
   content_type                    - Content type of the item

----------

Coach Content Recommendations.csv

This is the list of videos/audios that were recently recommended to you based on your and other users' viewing history.
   date                            - Date when the recommendation was generated
   id                              - Unique identifier of the item
   title                           - Name of the item
   bundle_id                       - Category of content in the Coach view that the item belongs to
   content_type                    - Content type of the item
   rating                          - Rating representing how good the recommendation was computed to be

----------

Coach Dynamic Recommendations.csv

This file contains the list of content rows that were personalized for you and that were embedded in pages in the app
other than the main Coach view.
   timestamp                       - Datetime of when the content row was determined
   component_id                    - Unique identifier of the content row
   bundle_id                       - Category of content in the Coach view that the item belongs to
   id                              - Unique identifier of the item
   title                           - Name of the item
   content_type                    - Content type of the item
   associated_tags                 - Tags describing the items in the content row and which can be filtered upon
