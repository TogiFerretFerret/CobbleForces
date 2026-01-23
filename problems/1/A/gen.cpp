#include <iostream>
#include <vector>
#include <string>
#include <random>
#include <cstdlib>

using namespace std;

/**
 * Standard C++ Generator for Problem A
 * Usage: ./gen [seed]
 */
int main(int argc, char* argv[]) {
    // Default seed
    int seed = 1;
    if (argc > 1) {
        seed = atoi(argv[1]);
    }
    
    // Initialize random number generator with the seed
    mt19937 rng(seed);
    
    // Determine N (1 to 1000)
    // We can use a different distribution logic if needed
    uniform_int_distribution<int> n_dist(1, 1000);
    int n = n_dist(rng);

    cout << n << endl;
    
    uniform_int_distribution<int> type_dist(0, 1);
    uniform_int_distribution<int> score_dist(1, 100);
    
    for (int i = 0; i < n; ++i) {
        // Randomly choose fandom
        string fandom = (type_dist(rng) == 0) ? "Bocchi" : "OshiNoKo";
        // Random score
        int score = score_dist(rng);
        
        cout << fandom << " " << score << endl;
    }
    
    return 0;
}
