#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <queue>
#include <algorithm>

using namespace std;

const int MOD = 1e9 + 7;

// --- TETRIS LOGIC ---

// Pieces represented as (row, col) offsets relative to top-left of the piece bounding box
// For standard spawn:
// I: ####
// O: ## / ##
// T: .#. / ###
// etc.
// We treat the "spawn" as a grid.
struct PieceShape {
    int h, w;
    vector<string> grid;
};

// Definitions matching the problem description
map<char, PieceShape> SHAPES = {
    {'I', {1, 4, {"####"}}},
    {'O', {2, 2, {"##", "##"}}},
    {'T', {2, 3, {".#.", "###"}}},
    {'L', {2, 3, {"..#", "###"}}},
    {'J', {2, 3, {"#..", "###"}}},
    {'S', {2, 3, {".##", "##."}}},
    {'Z', {2, 3, {"##.", ".##"}}}
};

// Represents the "Surface" of the board.
// Since we only care if it eventually clears, we prune states that get too high.
// For W=6, a max height of ~8 is sufficient to detect if we are in an unrecoverable state.
using Board = vector<string>; 

// Max height allowed before we declare state "dead" (impossible to clear back to 0)
const int MAX_PRUNE_HEIGHT = 8; 

// Simulate dropping a piece. Returns empty board if invalid/overflow.
Board simulate(Board b, char pType, int col, int W) {
    PieceShape p = SHAPES[pType];
    int c_idx = col - 1; // 0-indexed

    // 1. Determine drop height
    // We try to place the piece at row y (top of piece) such that it doesn't overlap
    // and is supported by something (floor or block).
    // Actually, simple gravity: start high, move down until collision.
    
    // Pad board with empty space to simulate drop
    int current_h = b.size();
    int start_y = current_h + 3; // Start safely above
    
    // Create a temporary large grid
    int temp_H = start_y + p.h + 2;
    vector<string> temp_grid(temp_H, string(W, '.'));
    
    // Copy existing board
    for(int r=0; r<current_h; ++r) temp_grid[r] = b[r];

    // Find lowest valid position
    int final_y = -1;
    
    for (int y = start_y; y >= 0; --y) {
        bool collision = false;
        // Check collision at this position
        for (int pr = 0; pr < p.h; ++pr) {
            for (int pc = 0; pc < p.w; ++pc) {
                if (p.grid[pr][pc] == '#') {
                    int board_r = y + (p.h - 1 - pr); // Flip because shapes are top-down visual, board is 0=bottom
                    // Wait, let's stick to standard array indexing: 0 = bottom
                    // Shape: row 0 is TOP visually.
                    // Let's define shape coordinate: grid[0] is TOP row.
                    // If we place piece top-left at (y_board, c_board):
                    // board[y_board - row_idx] matches shape[row_idx]
                    
                    int abs_r = y + (p.h - 1 - pr); 
                    
                    if (abs_r < 0) { collision = true; break; } // Floor collision
                    if (abs_r < current_h && b[abs_r][c_idx + pc] == '#') { collision = true; break; }
                }
            }
            if(collision) break;
        }
        
        if (collision) {
            // If we collided at y, the valid position was y+1
            final_y = y + 1;
            break;
        }
        if (y == 0) final_y = 0; // Reached floor
    }

    // Place piece
    int max_r_reached = 0;
    for (int pr = 0; pr < p.h; ++pr) {
        for (int pc = 0; pc < p.w; ++pc) {
            if (p.grid[pr][pc] == '#') {
                int abs_r = final_y + (p.h - 1 - pr);
                int abs_c = c_idx + pc;
                
                // Expand board if needed
                while (b.size() <= abs_r) b.push_back(string(W, '.'));
                b[abs_r][abs_c] = '#';
                max_r_reached = max(max_r_reached, abs_r);
            }
        }
    }

    // Clear lines
    vector<string> next_b;
    for (const string& row : b) {
        bool full = true;
        for (char c : row) if (c == '.') full = false;
        if (!full) next_b.push_back(row);
    }
    
    // Prune logic
    // If the board has holes deep down, it's represented in next_b.
    // If next_b is too tall, we assume it can never return to empty state (0).
    if (next_b.size() > MAX_PRUNE_HEIGHT) return {"INVALID"};
    
    return next_b;
}

// --- MATRIX LOGIC ---

typedef vector<vector<long long>> Matrix;

Matrix multiply(const Matrix& A, const Matrix& B) {
    int n = A.size();
    Matrix C(n, vector<long long>(n, 0));
    for (int i = 0; i < n; ++i)
        for (int k = 0; k < n; ++k)
            if (A[i][k])
                for (int j = 0; j < n; ++j)
                    C[i][j] = (C[i][j] + A[i][k] * B[k][j]) % MOD;
    return C;
}

Matrix power(Matrix A, long long p) {
    int n = A.size();
    Matrix Res(n, vector<long long>(n, 0));
    for (int i = 0; i < n; ++i) Res[i][i] = 1;
    while (p > 0) {
        if (p & 1) Res = multiply(Res, A);
        A = multiply(A, A);
        p >>= 1;
    }
    return Res;
}

// --- MAIN SOLVER ---

struct Edge {
    int v;
    char type;
    int col;
};

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int W, N;
    long long L;
    if (!(cin >> W >> N >> L)) return 0;

    int M;
    cin >> M;
    vector<vector<Edge>> adj(N + 1);
    for (int i = 0; i < M; ++i) {
        int u, v, c;
        char t;
        cin >> u >> v >> t >> c;
        adj[u].push_back({v, t, c});
    }

    // BFS to find reachable states (Node, Board)
    // Map State -> ID
    map<pair<int, Board>, int> state_to_id;
    vector<pair<int, Board>> id_to_state;
    queue<pair<int, Board>> q;

    Board empty_board; // size 0
    state_to_id[{1, empty_board}] = 0;
    id_to_state.push_back({1, empty_board});
    q.push({1, empty_board});

    int state_cnt = 0;

    // We build the transition matrix as we explore
    // Note: We need the full size first, but we don't know it.
    // So we build an adjacency list of transitions first: trans[from_id] -> list of (to_id)
    // Actually, we can just run BFS to discover all states, THEN build matrix.
    
    while(!q.empty()) {
        auto [u, board] = q.front();
        q.pop();
        
        // Try all edges
        for (auto& e : adj[u]) {
            Board next_b = simulate(board, e.type, e.col, W);
            if (next_b.size() == 1 && next_b[0] == "INVALID") continue;
            
            pair<int, Board> next_state = {e.v, next_b};
            if (state_to_id.find(next_state) == state_to_id.end()) {
                state_to_id[next_state] = ++state_cnt;
                id_to_state.push_back(next_state);
                q.push(next_state);
            }
        }
    }

    int total_states = state_cnt + 1;
    Matrix Mat(total_states, vector<long long>(total_states, 0));

    // Fill Matrix
    for (int i = 0; i < total_states; ++i) {
        auto [u, board] = id_to_state[i];
        for (auto& e : adj[u]) {
            Board next_b = simulate(board, e.type, e.col, W);
            if (next_b.size() == 1 && next_b[0] == "INVALID") continue;
            
            int j = state_to_id[{e.v, next_b}];
            Mat[i][j]++;
        }
    }

    // Exponentiate
    Matrix FinalMat = power(Mat, L);

    // Sum all paths ending in a state where Board is empty
    long long ans = 0;
    for (int i = 0; i < total_states; ++i) {
        // We started at ID 0. We want transitions 0 -> i
        if (FinalMat[0][i] > 0) {
            if (id_to_state[i].second.empty()) {
                ans = (ans + FinalMat[0][i]) % MOD;
            }
        }
    }

    cout << ans << endl;

    return 0;
}
