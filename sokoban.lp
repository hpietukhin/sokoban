%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% 4) GOAL: ALL CRATES ON GOALS AT THE SAME TIME
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
:- isgoal(L), isnongoal(L).
:- isgoal(L), wall(L).
:- clear(L,T), time(T), wall(L).

crate_on_goal(C,T) :- crate(C), at(C,L,T), isgoal(L), time(T).

goal_achieved(T) :-
    time(T),
    total_crates(N),
    N = #count { C : crate_on_goal(C,T) }.

% A plan is valid only when every crate is on a goal in the final state.
:- not goal_achieved(maxsteps).

% If the Sokoban S is in two different locations L1 and L2
% at the same moment T, this is forbidden.
:- sokoban(sokoban), at(sokoban, L1, T), at(sokoban, L2, T), L1 != L2.

% A crate C cannot be in (L1) and (L2) at moment T if L1 != L2
:- crate(C), at(C, L1, T), at(C, L2, T), L1 != L2.

% Two crates C1 and C2 cannot be in the same cell L at moment T
:- crate(C1), crate(C2), C1 != C2, at(C1, L, T), at(C2, L, T).

% Sokoban and a crate cannot be in the same cell L at moment T
:- crate(C), sokoban(sokoban), at(C, L, T), at(sokoban, L, T).

% Wall to the left or right of cell L
adjacentWallLeftOrRight(L) :- wall(L1), leftOf(L, L1).
adjacentWallLeftOrRight(L) :- wall(L1), leftOf(L1, L).

% Wall above or below cell L
adjacentWallAboveOrBelow(L) :- wall(L2), below(L, L2).
adjacentWallAboveOrBelow(L) :- wall(L2), below(L2, L).

% A cell is considered a deadlock if it is adjacent to two walls (left/right and above/below),
% and it is not a goal.
deadlock(L) :-
    location(L),
    adjacentWallLeftOrRight(L),
    adjacentWallAboveOrBelow(L),
    not isgoal(L).

% Prohibit moving a crate into a deadlock cell
:- do(pushLeft(S,X,Y,Z,C), T), deadlock(Z).
:- do(pushRight(S,X,Y,Z,C), T), deadlock(Z).
:- do(pushUp(S,X,Y,Z,C), T), deadlock(Z).
:- do(pushDown(S,X,Y,Z,C), T), deadlock(Z).

% Prohibit moving a crate into a wall
:- do(pushLeft(S,X,Y,Z,C), T), wall(Z).
:- do(pushRight(S,X,Y,Z,C), T), wall(Z).
:- do(pushUp(S,X,Y,Z,C), T), wall(Z).
:- do(pushDown(S,X,Y,Z,C), T), wall(Z).

% Prohibit moving Sokoban into a wall
:- do(moveLeft(S,X,Y), T), wall(Y).
:- do(moveRight(S,X,Y), T), wall(Y).
:- do(moveUp(S,X,Y), T), wall(Y).
:- do(moveDown(S,X,Y), T), wall(Y).
   
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% 5) ACTION SELECTION: exactly 1 action per step
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% For each T < maxsteps: choose 1 from all move/push (with appropriate parameters),
% or no action at all if desired - then change 1{..}1 to 0..1{..}.
%
% But below we generate a "boundary" set of ground actions through rules.
% 
% Method A: separate predicate do(Action,T). 
% Method B: directly "moveLeft(S,X,Y,T)" as an action. 
% I will show Method A to be closer to the classical notation:
    
0 { do(M,T) : move(M) } 1 :- time(T), T < maxsteps.

% Constraint: Sokoban cannot remain on the same cell in two consecutive steps
:- at(sokoban, L, T), at(sokoban, L, T+1), T < maxsteps, not goal_achieved(T).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% 6) DEFINING "move(M)" (GENERATING ALL POSSIBLE ACTIONS)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% --- moveLeft ---
move(moveLeft(S,X,Y)) :-
  sokoban(S),
  location(X;Y),
  leftOf(Y,X).

% --- moveRight ---
move(moveRight(S,X,Y)) :-
  sokoban(S),
  location(X;Y),
  leftOf(X,Y).

% --- moveUp ---
move(moveUp(S,X,Y)) :-
  sokoban(S),
  location(X;Y),
  below(X,Y).

% --- moveDown ---
move(moveDown(S,X,Y)) :-
  sokoban(S),
  location(X;Y),
  below(Y,X).

% --- pushLeft ---
move(pushLeft(S,X,Y,Z,C)) :-
  sokoban(S), crate(C),
  location(X;Y;Z),
  leftOf(Y,X),
  leftOf(Z,Y).

% --- pushRight ---
move(pushRight(S,X,Y,Z,C)) :-
  sokoban(S), crate(C),
  location(X;Y;Z),
  leftOf(X,Y),
  leftOf(Y,Z).

% --- pushUp ---
move(pushUp(S,X,Y,Z,C)) :-
  sokoban(S), crate(C),
  location(X;Y;Z),
  below(X,Y),
  below(Y,Z).

% --- pushDown ---
move(pushDown(S,X,Y,Z,C)) :-
  sokoban(S), crate(C),
  location(X;Y;Z),
  below(Y,X),
  below(Z,Y).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% 7) INERTIA (WITHOUT holds(...), a at(...,T) -> at(...,T+1)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% "If object O was in location L at moment T, and there is no proof
% that it stopped being there at moment T+1, then it remains."
at(O,L,T+1) :-
  at(O,L,T),
  not -at(O,L,T+1),
  time(T),
  T < maxsteps.

% Similarly for clear(L,T)
clear(L,T+1) :-
  clear(L,T),
  not -clear(L,T+1),
  time(T),
  T < maxsteps.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% 8) PRECONDITIONS (CONSTRAINTS)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% If the action moveLeft(S,X,Y) is selected, then Sokoban S MUST be at X at step T,
% and Y MUST be clear at step T.

% moveLeft
:- do(moveLeft(S,X,Y), T), not at(S,X,T).
:- do(moveLeft(S,X,Y), T), not clear(Y,T).

% moveRight
:- do(moveRight(S,X,Y), T), not at(S,X,T).
:- do(moveRight(S,X,Y), T), not clear(Y,T).

% moveUp
:- do(moveUp(S,X,Y), T), not at(S,X,T).
:- do(moveUp(S,X,Y), T), not clear(Y,T).

% moveDown
:- do(moveDown(S,X,Y), T), not at(S,X,T).
:- do(moveDown(S,X,Y), T), not clear(Y,T).

% pushLeft
:- do(pushLeft(S,X,Y,Z,C), T), not at(S,X,T), crate(C).
:- do(pushLeft(S,X,Y,Z,C), T), not at(C,Y,T), crate(C).
:- do(pushLeft(S,X,Y,Z,C), T), not clear(Z,T), crate(C).

% pushRight
:- do(pushRight(S,X,Y,Z,C), T), not at(S,X,T), crate(C).
:- do(pushRight(S,X,Y,Z,C), T), not at(C,Y,T), crate(C).
:- do(pushRight(S,X,Y,Z,C), T), not clear(Z,T), crate(C).

% pushUp
:- do(pushUp(S,X,Y,Z,C), T), not at(S,X,T), crate(C).
:- do(pushUp(S,X,Y,Z,C), T), not at(C,Y,T), crate(C).
:- do(pushUp(S,X,Y,Z,C), T), not clear(Z,T), crate(C).

% pushDown
:- do(pushDown(S,X,Y,Z,C), T), not at(S,X,T), crate(C).
:- do(pushDown(S,X,Y,Z,C), T), not at(C,Y,T), crate(C).
:- do(pushDown(S,X,Y,Z,C), T), not clear(Z,T), crate(C).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% 9) POSITIVE AND NEGATIVE EFFECTS
%%    EXPLICITLY at(...,T+1) AND -at(...,T+1)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%========== moveLeft ==========

% (a) If Sokoban moved from left to right, then at T+1 Sokoban is in Y
at(S, Y, T+1) :-
  do(moveLeft(S,X,Y), T),
  at(S,X,T),
  clear(Y,T).

% (b) Remove "Sokoban in X" at T+1
-at(S, X, T+1) :-
  do(moveLeft(S,X,Y), T),
  at(S,X,T).

% (c) The old cell X becomes clear
clear(X,T+1) :-
  do(moveLeft(S,X,Y), T),
  at(S,X,T),
  clear(Y,T).

% (d) The new cell Y is no longer clear
-clear(Y,T+1) :-
  do(moveLeft(S,X,Y), T),
  at(S,X,T),
  clear(Y,T).

%========== moveRight ==========

at(S,Y,T+1) :-
  do(moveRight(S,X,Y), T),
  at(S,X,T),
  clear(Y,T).

-at(S,X,T+1) :-
  do(moveRight(S,X,Y), T),
  at(S,X,T).

clear(X,T+1) :-
  do(moveRight(S,X,Y), T),
  at(S,X,T),
  clear(Y,T).

-clear(Y,T+1) :-
  do(moveRight(S,X,Y), T),
  at(S,X,T),
  clear(Y,T).

%========== moveUp ==========

at(S,Y,T+1) :-
  do(moveUp(S,X,Y), T),
  at(S,X,T),
  clear(Y,T).

-at(S,X,T+1) :-
  do(moveUp(S,X,Y), T),
  at(S,X,T).

clear(X,T+1) :-
  do(moveUp(S,X,Y), T),
  at(S,X,T),
  clear(Y,T).

-clear(Y,T+1) :-
  do(moveUp(S,X,Y), T),
  at(S,X,T),
  clear(Y,T).

%========== moveDown ==========

at(S,Y,T+1) :-
  do(moveDown(S,X,Y), T),
  at(S,X,T),
  clear(Y,T).

-at(S,X,T+1) :-
  do(moveDown(S,X,Y), T),
  at(S,X,T).

clear(X,T+1) :-
  do(moveDown(S,X,Y), T),
  at(S,X,T),
  clear(Y,T).

-clear(Y,T+1) :-
  do(moveDown(S,X,Y), T),
  at(S,X,T),
  clear(Y,T).

%========== pushLeft ==========

% pushLeft(S,X,Y,Z,C): Sokoban in X, crate in Y, Z is clear,
% pushing the crate from Y to Z, and Sokoban moves from X to Y

at(S, Y, T+1) :-
  do(pushLeft(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-at(S,X,T+1) :-
  do(pushLeft(S,X,Y,Z,C), T),
  at(S,X,T).

at(C, Z, T+1) :-
  do(pushLeft(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-at(C,Y,T+1) :-
  do(pushLeft(S,X,Y,Z,C), T),
  at(C,Y,T).

clear(X,T+1) :-
  do(pushLeft(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

% The new location Z is no longer clear
-clear(Z,T+1) :-
  do(pushLeft(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

% The location Y is now occupied by Sokoban, so it is no longer clear
-clear(Y,T+1) :-
  do(pushLeft(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

%========== pushRight ==========

at(S, Y, T+1) :-
  do(pushRight(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-at(S,X,T+1) :-
  do(pushRight(S,X,Y,Z,C), T),
  at(S,X,T).

at(C,Z,T+1) :-
  do(pushRight(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-at(C,Y,T+1) :-
  do(pushRight(S,X,Y,Z,C), T),
  at(C,Y,T).

clear(X,T+1) :-
  do(pushRight(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-clear(Z,T+1) :-
  do(pushRight(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-clear(Y,T+1) :-
  do(pushRight(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

%========== pushUp ==========

at(S,Y,T+1) :-
  do(pushUp(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-at(S,X,T+1) :-
  do(pushUp(S,X,Y,Z,C), T),
  at(S,X,T).

at(C,Z,T+1) :-
  do(pushUp(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-at(C,Y,T+1) :-
  do(pushUp(S,X,Y,Z,C), T),
  at(C,Y,T).

clear(X,T+1) :-
  do(pushUp(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-clear(Z,T+1) :-
  do(pushUp(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-clear(Y,T+1) :-
  do(pushUp(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

%========== pushDown ==========

at(S,Y,T+1) :-
  do(pushDown(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-at(S,X,T+1) :-
  do(pushDown(S,X,Y,Z,C), T),
  at(S,X,T).

at(C,Z,T+1) :-
  do(pushDown(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-at(C,Y,T+1) :-
  do(pushDown(S,X,Y,Z,C), T),
  at(C,Y,T).

clear(X,T+1) :-
  do(pushDown(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-clear(Z,T+1) :-
  do(pushDown(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

-clear(Y,T+1) :-
  do(pushDown(S,X,Y,Z,C), T),
  at(S,X,T),
  at(C,Y,T),
  clear(Z,T).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% 10) MINIMIZE THE NUMBER OF STEPS
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#minimize{1,T : do(M,T)}.
#minimize{T : do(_,T)}.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Constraints: The number of walls and crates does not change
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Define the total number of walls on the map
total_walls(N) :- N = #count{L : wall(L)}.

% Constraint: For each moment T, the number of walls remains equal to N
:- time(T), total_walls(N), N != #count{L : wall(L)}.

% Define the total number of crates on the map
total_crates(M) :- M = #count{C : crate(C)}.

% Constraint: For each moment T, the number of crates remains equal to M
:- time(T), total_crates(M), M != #count{C : at(C,L,T), crate(C)}.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% 11) OUTPUT ACTIONS
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#show do/2.
#show total_crates/1.
#show total_walls/1.