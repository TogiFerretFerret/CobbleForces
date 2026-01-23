#include <iostream>
#include <vector>
#include <string>
#include <algorithm>

using namespace std;

// Grid dimensions: 20 high, 10 wide.
// We use extra height to detect overflow safely.
bool grid[60][12]; // row 0-59, col 0-11 (1-10 used)

struct Point { int r, c; };

// Helper to define piece shapes relative to bottom-left (0,0) of the piece bounding box
vector<Point> get_shape(char type) {
    vector<Point> p;
    // Definitions based on prompt ASCII:
    if (type == 'I') {
        // #### (Width 4, Height 1)
        p = {{0,0}, {0,1}, {0,2}, {0,3}};
    } else if (type == 'O') {
        // ##
        // ##
        p = {{1,0}, {1,1}, {0,0}, {0,1}};
    } else if (type == 'T') {
        // .#. (Row 1)
        // ### (Row 0)
        p = {{1,1}, {0,0}, {0,1}, {0,2}};
    } else if (type == 'L') {
        // ..# (Row 1)
        // ### (Row 0)
        p = {{1,2}, {0,0}, {0,1}, {0,2}};
    } else if (type == 'J') {
        // #.. (Row 1)
        // ### (Row 0)
        p = {{1,0}, {0,0}, {0,1}, {0,2}};
    } else if (type == 'S') {
        // .## (Row 1)
        // ##. (Row 0)
        p = {{1,1}, {1,2}, {0,0}, {0,1}};
    } else if (type == 'Z') {
        // ##. (Row 1)
        // .## (Row 0)
        p = {{1,0}, {1,1}, {0,1}, {0,2}};
    }
    return p;
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int N;
    if (!(cin >> N)) return 0;
    
    // Initialize grid
    for(int r=0; r<60; r++) 
        for(int c=0; c<12; c++) 
            grid[r][c] = false;
            
    for (int i = 0; i < N; ++i) {
        char type;
        int col;
        cin >> type >> col;
        
        vector<Point> shape = get_shape(type);
        
        // Find drop height. Start checking from row 30 downwards.
        // We want to find the lowest 'r' such that placing the piece at 'r' is valid
        // but placing it at 'r-1' would collide.
        
        int best_r = 30; 
        
        // Move down until collision
        while (best_r > 0) {
            // Check if position (best_r - 1) is valid
            bool collision_below = false;
            int test_r = best_r - 1;
            
            if (test_r == 0) {
                collision_below = true; // Floor collision
            } else {
                for (auto p : shape) {
                    int abs_r = test_r + p.r;
                    int abs_c = col + p.c;
                    if (grid[abs_r][abs_c]) {
                        collision_below = true;
                        break;
                    }
                }
            }
            
            if (collision_below) {
                break; // We cannot move to test_r, so best_r is the spot
            }
            best_r--;
        }
        
        // Place piece at best_r
        int max_piece_height = 0;
        for (auto p : shape) {
            int final_r = best_r + p.r;
            int final_c = col + p.c;
            
            // Mark grid
            grid[final_r][final_c] = true;
            max_piece_height = max(max_piece_height, final_r);
        }
        
        // Check Game Over condition
        if (max_piece_height > 20) {
            cout << "Game Over" << endl;
            return 0;
        }
    }
    
    // Calculate final max height
    int max_h = 0;
    for (int r = 1; r <= 20; ++r) {
        for (int c = 1; c <= 10; ++c) {
            if (grid[r][c]) max_h = r;
        }
    }
    
    cout << max_h << endl;
    
    return 0;
}
