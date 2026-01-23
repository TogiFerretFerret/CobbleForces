#include <iostream>
#include <string>
#include <vector>

using namespace std;

/**
 * Solution for Problem B: The 727 Jumpscare (Subsequence Version)
 * * Logic:
 * We need to count triples (i, j, k) such that i < j < k and S[i]='7', S[j]='2', S[k]='7'.
 * * We can do this in O(N) using dynamic programming / running counters:
 * 1. cnt7: Count of '7's seen so far.
 * 2. cnt72: Count of "7...2" subsequences seen so far.
 * 3. total_727: Count of "7...2...7" subsequences.
 * * Algorithm:
 * Iterate through the string character by character:
 * - If current char is '7':
 * a. It completes any existing "7...2" pairs to form "7...2...7". So add `cnt72` to total.
 * b. It also counts as a new '7' for future pairs. So increment `cnt7`.
 * - If current char is '2':
 * a. It extends any existing '7's to form "7...2". So add `cnt7` to `cnt72`.
 * * Note: The logic order for '7' is important. A '7' cannot complete a "7...2" pair 
 * that uses *itself* as the first '7'. So we update total BEFORE incrementing cnt7.
 */
int main() {
    // Fast IO
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int N;
    if (!(cin >> N)) return 0;
    
    while (N--) {
        string s;
        cin >> s;
        
        long long cnt7 = 0;
        long long cnt72 = 0;
        long long total_727 = 0;
        
        for (char c : s) {
            if (c == '7') {
                // This 7 completes existing 7-2 pairs
                total_727 += cnt72;
                
                // This 7 also starts new sequences
                cnt7++;
            } else if (c == '2') {
                // This 2 combines with all previous 7s
                cnt72 += cnt7;
            }
        }
        
        cout << total_727 << "\n";
    }
    
    return 0;
}
