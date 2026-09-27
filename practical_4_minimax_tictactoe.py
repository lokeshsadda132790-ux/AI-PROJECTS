"""
Practical 4 - Artificial Intelligence (01AI0511)

Aim:
    Develop a game-playing agent using the minimax algorithm with
    alpha-beta pruning for Tic-Tac-Toe.

Approach:
    - The board is a list of 9 cells (' ' = empty, 'X' = human, 'O' = AI).
    - minimax() recursively explores every future sequence of moves,
      scoring a finished game as +10 (AI win), -10 (human win) or 0 (draw),
      adjusted by depth so the AI prefers a quicker win / a slower loss.
    - alpha and beta track the best score the maximizer (AI) and minimizer
      (human) can already guarantee; a branch is pruned (`break`) as soon
      as it cannot change the final decision, without changing the result.
    - Since Tic-Tac-Toe is a "solved" game, an AI that always plays the
      minimax-optimal move can never lose - at best you can force a draw.
"""

import math

HUMAN = 'X'
AI = 'O'
EMPTY = ' '

WIN_LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8),
             (0, 3, 6), (1, 4, 7), (2, 5, 8),
             (0, 4, 8), (2, 4, 6)]


def print_board(board):
    print()
    for i in range(0, 9, 3):
        r = board[i:i + 3]
        print(f" {r[0]} | {r[1]} | {r[2]} ")
        if i < 6:
            print("---+---+---")
    print()


def check_winner(board):
    """Returns 'X', 'O', 'Draw', or None (game still in progress)."""
    for a, b, c in WIN_LINES:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]
    if EMPTY not in board:
        return 'Draw'
    return None


def minimax(board, depth, is_maximizing, alpha, beta, node_counter):
    node_counter[0] += 1
    winner = check_winner(board)
    if winner == AI:
        return 10 - depth
    if winner == HUMAN:
        return depth - 10
    if winner == 'Draw':
        return 0

    if is_maximizing:
        best = -math.inf
        for i in range(9):
            if board[i] == EMPTY:
                board[i] = AI
                best = max(best, minimax(board, depth + 1, False, alpha, beta, node_counter))
                board[i] = EMPTY
                alpha = max(alpha, best)
                if beta <= alpha:
                    break  # beta cutoff: human already has a better option elsewhere
        return best
    else:
        best = math.inf
        for i in range(9):
            if board[i] == EMPTY:
                board[i] = HUMAN
                best = min(best, minimax(board, depth + 1, True, alpha, beta, node_counter))
                board[i] = EMPTY
                beta = min(beta, best)
                if beta <= alpha:
                    break  # alpha cutoff: AI already has a better option elsewhere
        return best


def best_move(board, verbose=True):
    """Chooses the AI's move by trying every empty cell and keeping the
    one minimax scores highest."""
    best_score = -math.inf
    move = None
    node_counter = [0]
    for i in range(9):
        if board[i] == EMPTY:
            board[i] = AI
            score = minimax(board, 0, False, -math.inf, math.inf, node_counter)
            board[i] = EMPTY
            if score > best_score:
                best_score = score
                move = i
    if verbose:
        print(f"[AI searched {node_counter[0]} nodes (with alpha-beta pruning) -> plays {move}]")
    return move


def play_game():
    board = [EMPTY] * 9
    print("Tic-Tac-Toe -- you are X, the AI is O.")
    print("Cells are numbered 0-8 like this:")
    print_board([str(i) for i in range(9)])

    turn = HUMAN
    while True:
        print_board(board)
        winner = check_winner(board)
        if winner:
            print("It's a draw!" if winner == 'Draw' else f"{winner} wins!")
            break

        if turn == HUMAN:
            move = None
            while move is None:
                raw = input("Your move (0-8): ").strip()
                if raw.isdigit() and 0 <= int(raw) <= 8 and board[int(raw)] == EMPTY:
                    move = int(raw)
                else:
                    print("Invalid move, try again.")
            board[move] = HUMAN
            turn = AI
        else:
            print("AI is thinking...")
            move = best_move(board)
            board[move] = AI
            turn = HUMAN


if __name__ == "__main__":
    play_game()
