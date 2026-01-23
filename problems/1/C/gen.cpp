#include <iostream>
#include <vector>
#include <string>
#include <random>
#include <cstdlib>

using namespace std;

// Definitions of piece widths to ensure valid inputs
int get_width(char type) {
    if (type == 'I') return 4;
    if (type == 'O') return 2;
    return 3; // T, L, J, S, Z
}

int main(int argc, char* argv[]) {
    int seed = 1;
    if (argc > 1) seed = atoi(argv[1]);
    mt19937 rng(seed);
    
    // N pieces
    int n = uniform_int_distribution<int>(5, 100)(rng);
    
    cout << n << endl;
    
    char types[] = {'I', 'O', 'T', 'L', 'J', 'S', 'Z'};
    
    for (int i = 0; i < n; ++i) {
        char t = types[uniform_int_distribution<int>(0, 6)(rng)];
        int w = get_width(t);
        
        // Ensure piece fits in 10-wide grid
        // If width is 4, max col is 7 (occupies 7, 8, 9, 10)
        int max_col = 10 - w + 1;
        int c = uniform_int_distribution<int>(1, max_col)(rng);
        
        cout << t << " " << c << endl;
    }
    
    return 0;
}
