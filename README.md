# mtg-cube.de web app

## Structure
### Apps
* Users

    * uses django-allauth's user template
* Tournaments

    * Follows the sitemap at https://octopus.do/zo48zz0581m

## Roadmap
### ToDos
#### Admin
* ~~Show all tournaments to superuser~~
* Add finish round button
#### Services
* Generate seatings
* Update standings on round finish
* Add groups/pods and phases (what even is a phase)
* Add deck image upload & check-in functionality
* Judge Call Button?
* ~~Notifications?~~
#### Views
* Add player pages
* Add cube list view (CubeCobra embed?)
#### Auth
* Add more OAuth providers
* Test own registration
* Add email service
#### Tests
* Test byes
* Test signup  
    * all oauths
    * normal registration
    * reset password
### Done
* Google OAuth
* Google One-Tap Login
* Tournament Admin View
* Tournament Player View
* Current Match Player View
* Standings View
* Round Timer
* Enrollment via All Events list
* Report & Confirm result functionality


---

### Draft Structure:

* Draft data model  
    * contains enrollments
    * number of rounds (3)
    * seatings
    * **Is a draft just a tournament?**  
        * maybe a draft is a "phase" - potential constructed tournaments don't have phases
* Admin assigns players into groups
* When generating pods, a random player gets generated and their entire group gets added to the pod
* Cube Data Model  
    * contains Name, Cubecobra link
    * gets assigned to a draft
    * keep track of which player has played which cube
