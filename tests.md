# Test Cases

## Accounts
### Account Creation
- [x] redirect to originally called page
- [x] display name gets populated on third-party login
- [ ] email address gets populated on third-party login

## Views
### Pool
- [ ] Checkin: Image upload changes status
- [ ] Checkout: Image upload changes status
- [ ] Checkin: Image deletion changes status
- [ ] Checkout: Image deletion changes status
### Standings
- [ ] Correct round number gets displayed after a round
- [ ] Correct round number gets displayed during a round


## Tournament Logic
### Enrollment
- [ ] registration is automatically confirmed
- [x] can't enroll in full events
- [ ] can't enroll in past events
### Pairing
- [ ] last player without a bye receives the bye
- [ ] no duplicate byes
- [ ] standings get generated even for this case  
(after rd. 2, 1 player has 6 pts, 4 players have 3 pts and 1 player has 0 pts):

    | Round | Match 1    | Match 2    | Match 3    |
    |-------|------------|------------|------------|
    | 1     | A vs B 2-0 | C vs D 2-0 | E vs F 2-0 |
    | 2     | A vs C 2-0 | B vs E 2-0 | D vs F 2-0 |
    | 3 (!) | A vs D     | B vs F     | C vs E     |

- [ ] dropped players don't get paired
### Standings
- [ ] standings don't update after result confirmation
- [ ] standings don't update after bye assignment
- [ ] tiebreakers get calculated correctly
### Results
- [ ] duplicate result reporting doesn't break scores
- [ ] admin confirmation for non-digital players doesn't break scores

