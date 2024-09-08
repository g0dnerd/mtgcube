# Notes
## General
- [x] breadcrumb has alert class?????
- [ ] breadcrumb format draft slug
## Event Registration
- [x] change from free spots to signups
- [x] disable event dashboard link & redirect
## Admin Event Dashboard
- update draft status:
    - [x] waiting for seatings
    - [x] waiting for pairings
    - [x] round in progress
- [x] event standings don't use cache properly like draft standings do
- [x] finish event round button should finish the phase as well when applicable
## Player Event Dashboard
- [x] match preview is broken with bye
- [x] remove match preview embed once round is finished -> status (waiting for next round)
- [x] reset draft button & match preview once draft is finished
- [x] event standings don't use cache properly like draft standings do
- [x] localize timetable
## Admin Draft Dashboard
- [x] redundant div borders after seatings before pairings
- [x] disable pair round button while round is in progress
- [x] remove reporting player when result is confirmed
- [x] finishing the last draft round needs to finish the draft, reset checkin and checkout status
## Player Draft Dashboard
- [x] pairing reveal & hide takes one extra refresh
- [x] waiting for pairings between rounds
- [x] bye doesn't get hidden on no check in
- [x] remove match embed and pairings once round is finished
- [x] Localize "Result" in match embed
- [x] Reminder when draft is finished but not checked out
- [x] add cube list as item
## Queries
- cache to round idx:
    - [x] current draft
    - [x] player pairings
    - [x] player match
## Services
### Pairings
- [x] continuous table numbers
### Event Standings
- [x] players not enrolled in any drafts should be ignored when making standings
- [x] handle identical standings