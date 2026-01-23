#include <iostream>
#include <vector>
#include <string>
#include <random>
#include <cstdlib>
#include <algorithm>

using namespace std;

/**
 * Generator for Problem B: The 727 Jumpscare (Harder Version)
 * Context: We are now checking for SUBSEQUENCES of "7-2-7".
 * We need to generate strings rich in 7s and 2s to force large answers
 * and test O(N) logic vs O(N^3) brute force.
 * Usage: ./gen [seed]
 */
int main(int argc, char* argv[]) {
    int seed = 1;
    if (argc > 1) {
        seed = atoi(argv[1]);
    }
    mt19937 rng(seed);
    
    // N (number of test strings) up to 20
    int n = uniform_int_distribution<int>(5, 20)(rng);
    cout << n << endl;
    
    for (int i = 0; i < n; ++i) {
        // Generate strings of varying lengths
        // Max length 5000 to keep it manageable but too slow for O(N^3) if we scale up later
        int len = uniform_int_distribution<int>(10, 5000)(rng);
        
        string s = "";
        // 50% chance to generate a "Brainrot" string (mostly 7s and 2s)
        // 50% chance to generate a random number string
        bool brainrot_mode = uniform_int_distribution<int>(0, 1)(rng);

        if (brainrot_mode) {
            for (int j = 0; j < len; ++j) {
                int r = uniform_int_distribution<int>(0, 100)(rng);
                if (r < 40) s += '7';      // 40% chance of 7
                else if (r < 70) s += '2'; // 30% chance of 2
                else s += (char)('0' + uniform_int_distribution<int>(0, 9)(rng)); // Noise
            }
        } else {
            // Standard random digits
            for (int j = 0; j < len; ++j) {
                s += (char)('0' + uniform_int_distribution<int>(0, 9)(rng));
            }
        }

        // Ensure no leading zeros if it's treated as a number, 
        // though for subsequence problems it's usually treated as a raw string.
        // We'll leave leading zeros as they add tricky edge cases if parsed as int.
        
        cout << s << endl;
    }
    
    return 0;
}
