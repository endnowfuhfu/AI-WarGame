# AI Board Game - COMP 472 (Deliverable 1)

## Introduction
This project is a board game developed for the Artificial Intelligence Class COMP 472. For Deliverable 1 (D1), the game supports manual play mode only (Human vs Human). Players can input their moves, which the program will validate and play, ultimately declaring a winner at the end of the game. The game trace can be stored in an output file for further analysis.

## Team Members
- Team Lead: Christopher Lopez (40199547)
- Kim Wei Kevin Chan (40176896)
- Xin Jia Cao (40207469)

## Features (Deliverable 1)
- Manual game mode (Human vs Human)
- Move validation
- Player move input through console
- Winner declaration at the end of the game
- Game trace storage in an output file

## How to Run the Program
1. Execute the `main.py` file:
    ```shell
    python main.py
    ```
2. The program will prompt you to enter the game parameters:
   - Maximum time (in seconds) allowed for the AI to return its move
   - Maximum number of turns for the game
   - Algorithm selection for the AI (alpha-beta (T) or minimax (F))
   - Play mode selection (For D1, select mode #1 - Human vs Human)
3. After setting the parameters, the game will commence. Players can move their pieces by:
   - Entering the location of the piece to move and the target location (e.g., `E2D2` will move the piece at location `E2` to location `D2`).
   - If the target location contains an enemy unit, your piece will attack.
   - Inputting the same location for the current and target locations (e.g., `E2E2`) will execute a self-destruct move.

## Game Play Instructions
- Players will take turns to input their moves.
- The program will validate each move before playing it.
- At the end of the game, the program will declare a winner and store the game trace in an output file.
