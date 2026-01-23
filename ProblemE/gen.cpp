#include <iostream>
#include <vector>
#include <string>
#include <random>
#include <chrono>

using namespace std;

// Piece definitions to ensure we generate valid columns
struct Piece {
    string type;
    int width;
};

const vector<Piece> PIECES = {
    {"I", 4}, {"O", 2}, {"T", 3}, {"L", 3}, {"J", 3}, {"S", 3}, {"Z", 3}
};

int main(int argc, char* argv[]) {
    // Seed setup
    unsigned int seed = std::chrono::system_clock::now().time_since_epoch().count();
    if (argc > 1) {
        seed = atoi(argv[1]);
    }
    mt19937_64 rng(seed);

    // Constraints
    // W: 1 to 6
    // N: 1 to 50
    // L: 1 to 10^18
    uniform_int_distribution<int> dist_W(4, 6); // Prefer slightly larger width for interesting cases
    uniform_int_distribution<int> dist_N(1, 10); // Keep N small for readable tests
    uniform_int_distribution<long long> dist_L(1, 1000000000000000000LL);
    
    int W = dist_W(rng);
    int N = dist_N(rng);
    long long L = dist_L(rng);

    cout << W << " " << N << " " << L << endl;

    // Edges M: 1 to 50
    uniform_int_distribution<int> dist_M(1, 2 * N); 
    int M = dist_M(rng);
    cout << M << endl;

    uniform_int_distribution<int> dist_node(1, N);
    uniform_int_distribution<int> dist_piece_idx(0, 6);

    for (int i = 0; i < M; ++i) {
        int u = dist_node(rng);
        int v = dist_node(rng);
        
        // Pick a piece that fits in W
        int p_idx = dist_piece_idx(rng);
        while (PIECES[p_idx].width > W) {
            p_idx = dist_piece_idx(rng);
        }
        
        // Pick a valid column
        // If width is W and piece width is w, col can be 1 to W-w+1
        int max_col = W - PIECES[p_idx].width + 1;
        uniform_int_distribution<int> dist_col(1, max_col);
        int col = dist_col(rng);

        cout << u << " " << v << " " << PIECES[p_idx].type << " " << col << endl;
    }

    return 0;
}
