# CFB_Betting
The application retrieves real-time and historical data about college football games and presents it in a structured, text-based interface.

# Functionality
* Allows users to pull the top 25 ranked teams in the nation  
* Users can view upcoming games upon requesting  
* Users can review previous games in the 2025 season  
* Allows users to create bet slips on upcoming games  
* Users can bet on 1, 3, 5, or 7 (legs) games at a time  
* Parleys with 3 or more legs increase the winnings multiplier based on the number of legs selected  
* Users can review current, previous, and all created bet slips  
* Bets can be deleted by a user until that game(s) is underway  
* Bet slips are saved to a `.db` file for long-term storage  
* Automatically settles bet slips upon a game's conclusion  

## Issues and Solutions

### 1. **Stale Pending Bets Not Updating**
**Issue:**  
Settled games were still showing as `PENDING` in the bet list.  

**Solution:**  
Added calls to `check_and_settle()` during initialization and before viewing slips to automatically update settled bets and display accurate statuses.

### 2. **User Bet Management**
**Issue:**  
Users could not manage their own bet slips effectively — canceled bets still appeared in the list or were locked incorrectly.  

**Solution:**  
Implemented a cancel feature inside `settlement_service` that allows users to remove a slip **only if no legs are underway**, ensuring integrity once games start.

### 3. **Slip Visibility and Organization**
**Issue:**  
The system displayed all slips in one view, making it hard to track current vs settled bets.  

**Solution:**  
Created three separate viewing actions:
- `View Current Slips (Pending)`
- `View Settled Slips (Won/Lost)`
- `View All Slips`  
This separation improved clarity and user experience.

### 4. **Data Synchronization at Startup**
**Issue:**  
When the program started, previously settled slips were not being reflected correctly in the database.  

**Solution:**  
Added an automatic settlement check in `init_db_and_wallet()` to ensure the wallet and slips are up-to-date upon program launch.

### 5. **CLI Needs Update**
**Issue:**  
The CLI for this application needs to be easier to read and navigate through.
**Solution:**  
Update the CLI layout for a cleaner/better look.

### 6. **Main.py Congestion**
**Issue:**  
The main.py file is rather cluttered.
**Solution:**  
Move the CLI menu and the actions to the helpers folder. Call the two files actions.py and menu.py then import them into the main.py script.

### 7. **Update Comments** 
**Issue:** 
Comments dont make a lot of sense because they were only for me to remember what I was last doing instead of explaining what the code is doing.
**Solution:**
Clean up comments on code and make them more robust for others to make sense of my code.