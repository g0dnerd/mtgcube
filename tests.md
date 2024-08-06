# Test Cases

## Accounts
### Account Creation
- [x] redirect to originally called page
- [x] populate display name on third-party login
- [ ] populate email address on third-party login

### Account Settings
- [ ] unique display names

## Tournaments
### Enrollment
- [ ] registration is automatically confirmed
- [ ] can't enroll in full events
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
    | 3     | A vs D     | B vs F     | C vs E     |
